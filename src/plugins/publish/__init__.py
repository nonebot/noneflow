from nonebot import logger, on_type
from nonebot.adapters.github import (
    GitHubBot,
    IssueCommentCreated,
    IssuesEdited,
    IssuesOpened,
    IssuesReopened,
    PullRequestClosed,
    PullRequestReviewSubmitted,
)
from nonebot.params import Depends

from .config import plugin_config
from .constants import BOT_MARKER, BRANCH_NAME_PREFIX, MAX_NAME_LENGTH
from .depends import (
    get_installation_id,
    get_issue_number,
    get_pull_requests_by_label,
    get_related_issue_number,
    get_repo_info,
    get_type_by_labels,
)
from .models import PublishType, RepoInfo
from .utils import (
    comment_issue,
    commit_and_push,
    create_pull_request,
    ensure_issue_content,
    extract_publish_info_from_issue,
    resolve_conflict_pull_requests,
    run_shell_command,
    should_skip_plugin_test,
    trigger_registry_update,
)
from .validation import PublishInfo


def bypass_git():
    """绕过检查"""
    # https://github.blog/2022-04-18-highlights-from-git-2-36/#stricter-repository-ownership-checks
    run_shell_command(["git", "config", "--global", "safe.directory", "*"])


def install_pre_commit_hooks():
    """安装 pre-commit 钩子"""
    run_shell_command(["pre-commit", "install", "--install-hooks"])


async def pr_close_rule(
    publish_type: PublishType | None = Depends(get_type_by_labels),
    related_issue_number: int | None = Depends(get_related_issue_number),
) -> bool:
    if publish_type is None:
        logger.info("拉取请求与发布无关，已跳过")
        return False

    if not related_issue_number:
        logger.error("无法获取相关的议题编号")
        return False

    return True


pr_close_matcher = on_type(PullRequestClosed, rule=pr_close_rule)


@pr_close_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_pr_close(
    event: PullRequestClosed,
    bot: GitHubBot,
    installation_id: int = Depends(get_installation_id),
    publish_type: PublishType = Depends(get_type_by_labels),
    repo_info: RepoInfo = Depends(get_repo_info),
    related_issue_number: int = Depends(get_related_issue_number),
) -> None:
    async with bot.as_installation(installation_id):
        issue = (
            await bot.rest.issues.async_get(
                **repo_info.dict(), issue_number=related_issue_number
            )
        ).parsed_data
        if issue.state == "open":
            logger.info(f"正在关闭议题 #{related_issue_number}")
            await bot.rest.issues.async_update(
                **repo_info.dict(),
                issue_number=related_issue_number,
                state="closed",
                state_reason="completed"
                if event.payload.pull_request.merged
                else "not_planned",
            )
        logger.info(f"议题 #{related_issue_number} 已关闭")

        # 如果商店更新则触发 registry 更新
        await trigger_registry_update(
            bot, publish_type, event.payload.pull_request, issue
        )

        try:
            run_shell_command(
                [
                    "git",
                    "push",
                    "origin",
                    "--delete",
                    event.payload.pull_request.head.ref,
                ]
            )
            logger.info(f"已删除对应分支")
        except:
            logger.info("对应分支不存在或已删除")

        if event.payload.pull_request.merged:
            logger.info("发布的拉取请求已合并，准备更新拉取请求的提交")
            pull_requests = await get_pull_requests_by_label(
                bot, repo_info, publish_type
            )
            await resolve_conflict_pull_requests(bot, repo_info, pull_requests)
        else:
            logger.info("发布的拉取请求未合并，已跳过")


async def check_rule(
    event: IssuesOpened | IssuesReopened | IssuesEdited | IssueCommentCreated,
    publish_type: PublishType | None = Depends(get_type_by_labels),
) -> bool:
    if isinstance(
        event, IssueCommentCreated
    ) and event.payload.comment.user.login.endswith(BOT_MARKER):
        logger.info("评论来自机器人，已跳过")
        return False
    if event.payload.issue.pull_request:
        logger.info("评论在拉取请求下，已跳过")
        return False
    if not publish_type:
        logger.info("议题与发布无关，已跳过")
        await publish_check_matcher.finish()

    return True


publish_check_matcher = on_type(
    (IssuesOpened, IssuesReopened, IssuesEdited, IssueCommentCreated),
    rule=check_rule,
)


@publish_check_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_publish_check(
    bot: GitHubBot,
    installation_id: int = Depends(get_installation_id),
    repo_info: RepoInfo = Depends(get_repo_info),
    issue_number: int = Depends(get_issue_number),
    publish_type: PublishType = Depends(get_type_by_labels),
) -> None:
    async with bot.as_installation(installation_id):
        # 因为 Actions 会排队，触发事件相关的议题在 Actions 执行时可能已经被关闭
        # 所以需要获取最新的议题状态
        issue = (
            await bot.rest.issues.async_get(
                **repo_info.dict(), issue_number=issue_number
            )
        ).parsed_data

        if issue.state != "open":
            logger.info("议题未开启，已跳过")
            await publish_check_matcher.finish()

        # 是否需要跳过插件测试
        plugin_config.skip_plugin_test = await should_skip_plugin_test(
            bot, repo_info, issue_number
        )

        # 如果需要跳过插件测试，则修改议题内容，确保其包含插件所需信息
        if publish_type == PublishType.PLUGIN and plugin_config.skip_plugin_test:
            await ensure_issue_content(bot, repo_info, issue_number, issue.body or "")  # type: ignore

        # 检查是否满足发布要求
        # 仅在通过检查的情况下创建拉取请求
        info = extract_publish_info_from_issue(issue, publish_type)

        # 设置拉取请求与议题的标题
        if isinstance(info, PublishInfo):
            name = info.name
        else:
            name = info.raw_data.get("name") or ""
        # 限制标题长度，过长的标题不好看
        title = f"{publish_type.value}: {name[:MAX_NAME_LENGTH]}"

        if isinstance(info, PublishInfo):
            # 创建新分支
            # 命名示例 publish/issue123
            branch_name = f"{BRANCH_NAME_PREFIX}{issue_number}"
            run_shell_command(["git", "switch", "-C", branch_name])
            # 更新文件并提交更改
            info.update_file()
            commit_and_push(info, branch_name, issue_number)
            # 创建拉取请求
            await create_pull_request(
                bot, repo_info, info, branch_name, issue_number, title
            )
            message = info.validation_message
        else:
            message = info.message
            logger.info("发布没通过检查，暂不创建拉取请求")

        # 修改议题标题
        # 需要等创建完拉取请求并打上标签后执行
        # 不然会因为修改议题触发 Actions 导致标签没有正常打上
        if issue.title != title:
            await bot.rest.issues.async_update(
                **repo_info.dict(), issue_number=issue_number, title=title
            )
            logger.info(f"议题标题已修改为 {title}")

        await comment_issue(bot, repo_info, issue_number, message)


async def review_submiited_rule(
    event: PullRequestReviewSubmitted,
    publish_type: PublishType | None = Depends(get_type_by_labels),
) -> bool:
    if publish_type is None:
        logger.info("拉取请求与发布无关，已跳过")
        return False
    if event.payload.review.author_association not in ["OWNER", "MEMBER"]:
        logger.info("审查者不是仓库成员，已跳过")
        return False
    if event.payload.review.state != "approved":
        logger.info("未通过审查，已跳过")
        return False

    return True


auto_merge_matcher = on_type(PullRequestReviewSubmitted, rule=review_submiited_rule)


@auto_merge_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_auto_merge(
    bot: GitHubBot,
    event: PullRequestReviewSubmitted,
    installation_id: int = Depends(get_installation_id),
    repo_info: RepoInfo = Depends(get_repo_info),
) -> None:
    async with bot.as_installation(installation_id):
        pull_request = (
            await bot.rest.pulls.async_get(
                **repo_info.dict(), pull_number=event.payload.pull_request.number
            )
        ).parsed_data

        if not pull_request.mergeable:
            # 需要先获取远程分支，否则无法切换到对应分支
            run_shell_command(
                ["git", "fetch", "origin", plugin_config.input_config.base]
            )
            # 尝试处理冲突
            await resolve_conflict_pull_requests(bot, repo_info, [pull_request])

        await bot.rest.pulls.async_merge(
            **repo_info.dict(),
            pull_number=event.payload.pull_request.number,
            merge_method="rebase",
        )
        logger.info(f"已自动合并 #{event.payload.pull_request.number}")
