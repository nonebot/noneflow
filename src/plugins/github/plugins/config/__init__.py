from githubkit.exception import RequestFailed
from nonebot import logger, on_type
from nonebot.adapters.github import GitHubBot
from nonebot.adapters.github.event import (
    IssueCommentCreated,
    IssuesEdited,
    IssuesOpened,
    IssuesReopened,
    PullRequestReviewSubmitted,
)
from nonebot.params import Depends

from src.plugins.github.constants import CONFIG_LABEL, TITLE_MAX_LENGTH
from src.plugins.github.depends import (
    bypass_git,
    get_github_handler,
    get_installation_id,
    get_issue_handler,
    is_bot_triggered_workflow,
    is_config_workflow,
)
from src.plugins.github.handlers import GithubHandler, IssueHandler
from src.plugins.github.plugins.publish.render import render_comment
from src.plugins.github.plugins.publish.utils import (
    ensure_issue_plugin_test_button,
    ensure_issue_plugin_test_button_in_progress,
)
from src.plugins.github.typing import IssuesEvent

from .constants import BRANCH_NAME_PREFIX, COMMIT_MESSAGE_PREFIX, RESULTS_BRANCH
from .utils import (
    update_file,
    validate_info_from_issue,
)


async def check_rule(
    event: IssuesEvent,
    is_bot: bool = Depends(is_bot_triggered_workflow),
    is_config: bool = Depends(is_config_workflow),
) -> bool:
    if is_bot:
        logger.info("机器人触发的工作流，已跳过")
        return False
    if event.payload.issue.pull_request:
        logger.info("评论在拉取请求下，已跳过")
        return False
    if not is_config:
        logger.info("非配置工作流，已跳过")
        return False
    return True


config_check_matcher = on_type(
    (IssuesOpened, IssuesReopened, IssuesEdited, IssueCommentCreated), rule=check_rule
)


@config_check_matcher.handle(parameterless=[Depends(bypass_git)])
async def handle_remove_check(
    bot: GitHubBot,
    installation_id: int = Depends(get_installation_id),
    handler: IssueHandler = Depends(get_issue_handler),
):
    async with bot.as_installation(installation_id):
        if handler.issue.state != "open":
            logger.info("议题未开启，已跳过")
            await config_check_matcher.finish()

        # 提示插件正在测试中
        await ensure_issue_plugin_test_button_in_progress(handler)

        # 需要先切换到结果分支
        handler.checkout_remote_branch(RESULTS_BRANCH)

        # 检查是否满足发布要求
        # 仅在通过检查的情况下创建拉取请求
        result = await validate_info_from_issue(handler)

        # 渲染评论信息
        comment = await render_comment(result, True)

        # 对议题评论
        await handler.resuable_comment_issue(comment)

        branch_name = f"{BRANCH_NAME_PREFIX}{handler.issue_number}"

        # 设置拉取请求与议题的标题
        # 限制标题长度，过长的标题不好看
        title = f"{result.type}: {result.name[:TITLE_MAX_LENGTH]}"

        # 修改议题标题
        await handler.update_issue_title(title)

        if result.valid:
            commit_message = f"{COMMIT_MESSAGE_PREFIX} {result.type.value.lower()} {result.name} (#{handler.issue_number})"

            # 创建新分支
            handler.switch_branch(branch_name)
            # 更新文件
            update_file(result, handler)
            handler.commit_and_push(commit_message, branch_name, handler.author)
            # 创建拉取请求
            try:
                pull_number = await handler.create_pull_request(
                    RESULTS_BRANCH,
                    title,
                    branch_name,
                )
                await handler.add_labels(
                    pull_number,
                    [result.type.value, CONFIG_LABEL],
                )
            except RequestFailed:
                await handler.update_pull_request_status(title, branch_name)
                logger.info("该分支的拉取请求已创建，请前往查看")
        else:
            # 如果之前已经创建了拉取请求，则将其转换为草稿
            await handler.draft_pull_request(branch_name)

        # 确保插件重测按钮存在
        await ensure_issue_plugin_test_button(handler)


async def review_submitted_rule(
    event: PullRequestReviewSubmitted,
    is_config: bool = Depends(is_config_workflow),
) -> bool:
    if not is_config:
        logger.info("拉取请求与配置无关，已跳过")
        return False
    if event.payload.review.author_association not in ["OWNER", "MEMBER"]:
        logger.info("审查者不是仓库成员，已跳过")
        return False
    if event.payload.review.state != "approved":
        logger.info("未通过审查，已跳过")
        return False

    return True


auto_merge_matcher = on_type(PullRequestReviewSubmitted, rule=review_submitted_rule)


@auto_merge_matcher.handle(parameterless=[Depends(bypass_git)])
async def handle_auto_merge(
    bot: GitHubBot,
    event: PullRequestReviewSubmitted,
    installation_id: int = Depends(get_installation_id),
    handler: GithubHandler = Depends(get_github_handler),
) -> None:
    async with bot.as_installation(installation_id):
        pull_number = event.payload.pull_request.number

        # 如果有冲突的话，不会触发 Github Actions
        # 所以直接合并即可
        await handler.merge_pull_request(pull_number, "rebase")

        logger.info(f"已自动合并 #{event.payload.pull_request.number}")
