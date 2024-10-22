from typing import Literal
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
from nonebot.params import Depends, Arg
from nonebot.typing import T_State

from src.plugins.github.constants import BRANCH_NAME_PREFIX, TITLE_MAX_LENGTH
from src.plugins.github.plugins.publish.render import render_comment
from src.providers.validation.models import PublishType, ValidationDict

from src.plugins.github.depends import (
    bypass_git,
    get_github_handler,
    get_installation_id,
    get_issue_number,
    get_repo_info,
    get_related_issue_number,
    install_pre_commit_hooks,
    is_bot_triggered_workflow,
)
from src.plugins.github.models import GithubHandler, IssueHandler, RepoInfo
from src.plugins.github import plugin_config


from .depends import (
    get_type_by_labels,
)

from .utils import (
    ensure_issue_content,
    ensure_issue_test_button,
    process_pull_request,
    resolve_conflict_pull_requests,
    is_plugin_test_button_check,
    should_skip_plugin_test,
    trigger_registry_update,
)
from .validation import (
    validate_adapter_info_from_issue,
    validate_bot_info_from_issue,
    validate_plugin_info_from_issue,
)


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
                **repo_info.model_dump(), issue_number=related_issue_number
            )
        ).parsed_data

        handler = IssueHandler(
            bot=bot, repo_info=repo_info, issue_number=related_issue_number, issue=issue
        )

        if issue.state == "open":
            reason = "completed" if event.payload.pull_request.merged else "not_planned"
            await handler.close_issue(reason)
        logger.info(f"议题 #{related_issue_number} 已关闭")

        try:
            handler.delete_origin_branch(event.payload.pull_request.head.ref)
            logger.info("已删除对应分支")
        except Exception:
            logger.info("对应分支不存在或已删除")

        if event.payload.pull_request.merged:
            logger.info("发布的拉取请求已合并，准备更新拉取请求的提交")
            pull_requests = await handler.get_pull_requests_by_label(publish_type.value)
            await resolve_conflict_pull_requests(handler, pull_requests)
        else:
            logger.info("发布的拉取请求未合并，已跳过")

        # 如果商店更新则触发 registry 更新
        if event.payload.pull_request.merged:
            await trigger_registry_update(bot, repo_info, publish_type, issue)
        else:
            logger.info("拉取请求未合并，跳过触发商店列表更新")


async def check_rule(
    event: IssuesOpened | IssuesReopened | IssuesEdited | IssueCommentCreated,
    publish_type: PublishType | None = Depends(get_type_by_labels),
    is_bot: bool = Depends(is_bot_triggered_workflow),
) -> bool:
    if is_bot:
        logger.info("机器人触发的工作流，已跳过")
        return False
    if event.payload.issue.pull_request:
        logger.info("评论在拉取请求下，已跳过")
        return False
    if not publish_type:
        logger.info("议题与发布无关，已跳过")
        return False

    return True


publish_check_matcher = on_type(
    (IssuesOpened, IssuesReopened, IssuesEdited, IssueCommentCreated),
    rule=check_rule,
)


@publish_check_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_publish_plugin_check(
    bot: GitHubBot,
    state: T_State,
    installation_id: int = Depends(get_installation_id),
    repo_info: RepoInfo = Depends(get_repo_info),
    issue_number: int = Depends(get_issue_number),
    publish_type: Literal[PublishType.PLUGIN] = Depends(get_type_by_labels),
) -> None:
    async with bot.as_installation(installation_id):
        # 因为 Actions 会排队，触发事件相关的议题在 Actions 执行时可能已经被关闭
        # 所以需要获取最新的议题状态
        issue = (
            await bot.rest.issues.async_get(
                **repo_info.model_dump(), issue_number=issue_number
            )
        ).parsed_data

        handler = IssueHandler(
            issue=issue, bot=bot, repo_info=repo_info, issue_number=issue_number
        )

        if issue.state != "open":
            logger.info("议题未开启，已跳过")
            await publish_check_matcher.finish()
        if is_plugin_test_button_check(issue):
            logger.info("测试按钮已勾选，跳过插件发布检查")
            await publish_check_matcher.finish()

        # 是否需要跳过插件测试
        plugin_config.skip_plugin_test = await should_skip_plugin_test(
            bot, repo_info, issue_number
        )
        # 如果需要跳过插件测试，则修改议题内容，确保其包含插件所需信息
        if plugin_config.skip_plugin_test:
            await ensure_issue_content(handler)

        # 检查是否满足发布要求
        # 仅在通过检查的情况下创建拉取请求
        result = await validate_plugin_info_from_issue(issue)

        # 确保插件重测按钮存在
        await ensure_issue_test_button(handler)

        state["handler"] = handler
        state["validation"] = result


@publish_check_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_adapter_publish_check(
    bot: GitHubBot,
    state: T_State,
    installation_id: int = Depends(get_installation_id),
    repo_info: RepoInfo = Depends(get_repo_info),
    issue_number: int = Depends(get_issue_number),
    publish_type: Literal[PublishType.ADAPTER] = Depends(get_type_by_labels),
) -> None:
    async with bot.as_installation(installation_id):
        # 因为 Actions 会排队，触发事件相关的议题在 Actions 执行时可能已经被关闭
        # 所以需要获取最新的议题状态
        issue = (
            await bot.rest.issues.async_get(
                **repo_info.model_dump(), issue_number=issue_number
            )
        ).parsed_data

        handler = IssueHandler(
            issue=issue, bot=bot, repo_info=repo_info, issue_number=issue_number
        )

        if issue.state != "open":
            logger.info("议题未开启，已跳过")
            await publish_check_matcher.finish()

        # 检查是否满足发布要求
        # 仅在通过检查的情况下创建拉取请求
        result = await validate_adapter_info_from_issue(issue)

        state["handler"] = handler
        state["validation"] = result


@publish_check_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_bot_publish_check(
    bot: GitHubBot,
    state: T_State,
    installation_id: int = Depends(get_installation_id),
    repo_info: RepoInfo = Depends(get_repo_info),
    issue_number: int = Depends(get_issue_number),
    publish_type: Literal[PublishType.BOT] = Depends(get_type_by_labels),
) -> None:
    async with bot.as_installation(installation_id):
        # 因为 Actions 会排队，触发事件相关的议题在 Actions 执行时可能已经被关闭
        # 所以需要获取最新的议题状态

        issue = (
            await bot.rest.issues.async_get(
                **repo_info.model_dump(), issue_number=issue_number
            )
        ).parsed_data

        handler = IssueHandler(
            issue=issue, bot=bot, repo_info=repo_info, issue_number=issue_number
        )

        if issue.state != "open":
            logger.info("议题未开启，已跳过")
            await publish_check_matcher.finish()

        # 检查是否满足发布要求
        # 仅在通过检查的情况下创建拉取请求
        result = await validate_bot_info_from_issue(issue)

        state["handler"] = handler
        state["validation"] = result


@publish_check_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_pull_request_and_update_issue(
    bot: GitHubBot,
    handler: IssueHandler = Arg(),
    validation: ValidationDict = Arg(),
    installation_id: int = Depends(get_installation_id),
) -> None:
    async with bot.as_installation(installation_id):
        branch_name = f"{BRANCH_NAME_PREFIX}{handler.issue_number}"

        # 设置拉取请求与议题的标题
        # 限制标题长度，过长的标题不好看
        title = f"{validation.type}: {validation.name[:TITLE_MAX_LENGTH]}"

        # 渲染评论信息
        comment = await render_comment(validation, True)

        # 验证之后创建拉取请求和修改议题的标题
        await process_pull_request(handler, validation, branch_name, title)

        # 修改议题标题
        await handler.update_issue_title(title)

        # 对议题评论
        await handler.comment_issue(comment)


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
    handler: GithubHandler = Depends(get_github_handler),
) -> None:
    async with bot.as_installation(installation_id):
        pull_request = (
            await bot.rest.pulls.async_get(
                **repo_info.model_dump(), pull_number=event.payload.pull_request.number
            )
        ).parsed_data

        if not pull_request.mergeable:
            # 尝试处理冲突
            await resolve_conflict_pull_requests(handler, [pull_request])

        await bot.rest.pulls.async_merge(
            **repo_info.model_dump(),
            pull_number=event.payload.pull_request.number,
            merge_method="rebase",
        )
        logger.info(f"已自动合并 #{event.payload.pull_request.number}")
