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
from pydantic_core import PydanticCustomError

from src.plugins.github import plugin_config
from src.plugins.github.constants import TITLE_MAX_LENGTH
from src.plugins.github.depends import (
    get_github_handler,
    get_installation_id,
    get_issue_handler,
    get_related_issue_number,
    get_type_by_labels_name,
    is_bot_triggered_workflow,
    is_remove_workflow,
    setup_git,
)
from src.plugins.github.handlers import GithubHandler, IssueHandler
from src.plugins.github.typing import IssuesEvent
from src.providers.validation.models import PublishType

from .constants import BRANCH_NAME_PREFIX
from .render import render_comment, render_error
from .utils import process_pull_requests
from .validation import validate_author_info


async def pr_close_rule(
    is_remove: bool = Depends(is_remove_workflow),
    related_issue_number: int | None = Depends(get_related_issue_number),
) -> bool:
    if not is_remove:
        logger.info("拉取请求与删除无关，已跳过")
        return False

    if not related_issue_number:
        logger.error("无法获取相关的议题编号")
        return False

    return True


async def check_rule(
    event: IssuesEvent,
    is_remove: bool = Depends(is_remove_workflow),
    is_bot: bool = Depends(is_bot_triggered_workflow),
) -> bool:
    if is_bot:
        logger.info("机器人触发的工作流，已跳过")
        return False
    if event.payload.issue.pull_request:
        logger.info("评论在拉取请求下，已跳过")
        return False
    if not is_remove:
        logger.info("非删除工作流，已跳过")
        return False
    return True


remove_check_matcher = on_type(
    (IssuesOpened, IssuesReopened, IssuesEdited, IssueCommentCreated), rule=check_rule
)


@remove_check_matcher.handle(parameterless=[Depends(setup_git)])
async def handle_remove_check(
    bot: GitHubBot,
    installation_id: int = Depends(get_installation_id),
    handler: IssueHandler = Depends(get_issue_handler),
    publish_type: PublishType = Depends(get_type_by_labels_name),
):
    async with bot.as_installation(installation_id):
        if handler.issue.state != "open":
            logger.info("议题未开启，已跳过")
            await remove_check_matcher.finish()

        try:
            # 搜索包的信息和验证作者信息
            result = await validate_author_info(handler.issue, publish_type)
        except PydanticCustomError as err:
            logger.error(f"信息验证失败: {err}")
            await handler.resuable_comment_issue(await render_error(err))
            await remove_check_matcher.finish()

        title = f"{result.publish_type}: Remove {result.name or 'Unknown'}"[
            :TITLE_MAX_LENGTH
        ]
        branch_name = f"{BRANCH_NAME_PREFIX}{handler.issue_number}"

        # 根据 input_config 里的 remove 仓库来进行提交和 PR
        store_handler = GithubHandler(
            bot=handler.bot, repo_info=plugin_config.input_config.store_repository
        )
        # 处理拉取请求和议题标题
        await process_pull_requests(handler, store_handler, result, branch_name, title)

        await handler.update_issue_title(title)

        # 获取 pull request 编号
        pull_number = (
            await store_handler.get_pull_request_by_branch(branch_name)
        ).number

        # 评论议题
        comment = await render_comment(
            result,
            f"{plugin_config.input_config.store_repository}#{pull_number}",
        )
        await handler.resuable_comment_issue(comment)


async def review_submitted_rule(
    event: PullRequestReviewSubmitted,
    is_remove: bool = Depends(is_remove_workflow),
) -> bool:
    if not is_remove:
        logger.info("拉取请求与删除无关，已跳过")
        return False
    if event.payload.review.author_association not in ["OWNER", "MEMBER"]:
        logger.info("审查者不是仓库成员，已跳过")
        return False
    if event.payload.review.state != "approved":
        logger.info("未通过审查，已跳过")
        return False

    return True


auto_merge_matcher = on_type(PullRequestReviewSubmitted, rule=review_submitted_rule)


@auto_merge_matcher.handle(parameterless=[Depends(setup_git)])
async def handle_auto_merge(
    bot: GitHubBot,
    event: PullRequestReviewSubmitted,
    installation_id: int = Depends(get_installation_id),
    handler: GithubHandler = Depends(get_github_handler),
) -> None:
    async with bot.as_installation(installation_id):
        pull_number = event.payload.pull_request.number

        await handler.merge_pull_request(pull_number, "rebase")

        logger.info(f"已自动合并 #{pull_number}")
