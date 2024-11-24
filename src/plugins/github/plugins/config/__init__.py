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
    RepoInfo,
    bypass_git,
    get_installation_id,
    get_issue_handler,
    get_repo_info,
    get_type_by_labels_name,
    install_pre_commit_hooks,
    is_bot_triggered_workflow,
)
from src.plugins.github.models import IssueHandler
from src.plugins.github.plugins.publish.render import render_comment
from src.plugins.github.plugins.publish.validation import (
    validate_plugin_info_from_issue,
)
from src.plugins.github.plugins.remove.depends import check_labels
from src.plugins.github.typing import IssuesEvent
from src.providers.validation.models import PublishType

from .constants import BRANCH_NAME_PREFIX
from .utils import process_pull_request


async def check_rule(
    event: IssuesEvent,
    is_config: bool = check_labels(CONFIG_LABEL),
    is_bot: bool = Depends(is_bot_triggered_workflow),
    publish_type: PublishType = Depends(get_type_by_labels_name),
) -> bool:
    if is_bot:
        logger.info("机器人触发的工作流，已跳过")
        return False
    if publish_type != PublishType.PLUGIN:
        logger.info("与插件无关，已跳过")
        return False
    if event.payload.issue.pull_request:
        logger.info("评论在拉取请求下，已跳过")
        return False
    if is_config is False:
        logger.info("非配置工作流，已跳过")
        return False
    return True


config_check_matcher = on_type(
    (IssuesOpened, IssuesReopened, IssuesEdited, IssueCommentCreated), rule=check_rule
)


@config_check_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_remove_check(
    bot: GitHubBot,
    installation_id: int = Depends(get_installation_id),
    handler: IssueHandler = Depends(get_issue_handler),
):
    async with bot.as_installation(installation_id):
        if handler.issue.state != "open":
            logger.info("议题未开启，已跳过")
            await config_check_matcher.finish()

        # 检查是否满足发布要求
        # 仅在通过检查的情况下创建拉取请求
        result = await validate_plugin_info_from_issue(handler)

        branch_name = f"{BRANCH_NAME_PREFIX}{handler.issue_number}"

        # 设置拉取请求与议题的标题
        # 限制标题长度，过长的标题不好看
        title = f"{result.type}: {result.name[:TITLE_MAX_LENGTH]}"

        # 渲染评论信息
        comment = await render_comment(result, True)

        # 验证之后创建拉取请求
        await process_pull_request(handler, result, branch_name, title)

        # 对议题评论
        await handler.comment_issue(comment)


async def review_submitted_rule(
    event: PullRequestReviewSubmitted,
    is_config: bool = check_labels(CONFIG_LABEL),
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
        # 如果有冲突的话，不会触发 Github Actions
        # 所以直接合并即可
        await bot.rest.pulls.async_merge(
            **repo_info.model_dump(),
            pull_number=event.payload.pull_request.number,
            merge_method="rebase",
        )
        logger.info(f"已自动合并 #{event.payload.pull_request.number}")
