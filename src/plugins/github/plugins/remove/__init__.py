from nonebot import logger, on_type
from nonebot.adapters.github import GitHubBot
from nonebot.adapters.github.event import (
    IssueCommentCreated,
    IssuesEdited,
    IssuesOpened,
    IssuesReopened,
    PullRequestClosed,
)
from nonebot.params import Depends
from pydantic_core import PydanticCustomError

from src.plugins.github import plugin_config
from src.plugins.github.constants import TITLE_MAX_LENGTH
from src.plugins.github.depends import (
    RepoInfo,
    bypass_git,
    get_installation_id,
    get_issue_number,
    get_related_issue_number,
    get_repo_info,
    get_type_by_labels_name,
    install_pre_commit_hooks,
    is_bot_triggered_workflow,
)
from src.plugins.github.models import IssueHandler
from src.plugins.github.models.github import GithubHandler
from src.plugins.github.typing import IssuesEvent
from src.providers.validation.models import PublishType

from .constants import BRANCH_NAME_PREFIX, REMOVE_LABEL
from .depends import check_labels
from .render import render_comment, render_error
from .utils import process_pull_reqeusts, resolve_conflict_pull_requests
from .validation import validate_author_info


async def pr_close_rule(
    is_remove: bool = check_labels(REMOVE_LABEL),
    related_issue_number: int | None = Depends(get_related_issue_number),
) -> bool:
    if not is_remove:
        logger.info("拉取请求与删除无关，已跳过")
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
    repo_info: RepoInfo = Depends(get_repo_info),
    related_issue_number: int = Depends(get_related_issue_number),
) -> None:
    async with bot.as_installation(installation_id):
        issue = (
            await bot.rest.issues.async_get(
                **repo_info.model_dump(), issue_number=related_issue_number
            )
        ).parsed_data

        handler = IssueHandler(bot=bot, repo_info=repo_info, issue=issue)

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
            logger.info("发布的拉取请求已合并，准备更新其它拉取请求的提交")
            pull_requests = await handler.get_pull_requests_by_label(REMOVE_LABEL)
            await resolve_conflict_pull_requests(handler, pull_requests)
        else:
            logger.info("发布的拉取请求未合并，已跳过")


async def check_rule(
    event: IssuesEvent,
    is_remove: bool = check_labels(REMOVE_LABEL),
    is_bot: bool = Depends(is_bot_triggered_workflow),
) -> bool:
    if is_bot:
        logger.info("机器人触发的工作流，已跳过")
        return False
    if event.payload.issue.pull_request:
        logger.info("评论在拉取请求下，已跳过")
        return False
    if is_remove is False:
        logger.info("非删除工作流，已跳过")
        return False
    return True


remove_check_matcher = on_type(
    (IssuesOpened, IssuesReopened, IssuesEdited, IssueCommentCreated), rule=check_rule
)


@remove_check_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_remove_check(
    bot: GitHubBot,
    installation_id: int = Depends(get_installation_id),
    repo_info: RepoInfo = Depends(get_repo_info),
    issue_number: int = Depends(get_issue_number),
    publish_type: PublishType = Depends(get_type_by_labels_name),
):
    async with bot.as_installation(installation_id):
        issue = (
            await bot.rest.issues.async_get(
                **repo_info.model_dump(), issue_number=issue_number
            )
        ).parsed_data

        if issue.state != "open":
            logger.info("议题未开启，已跳过")
            await remove_check_matcher.finish()
        handler = IssueHandler(bot=bot, repo_info=repo_info, issue=issue)

        try:
            # 搜索包的信息和验证作者信息
            result = await validate_author_info(issue, publish_type)
        except PydanticCustomError as err:
            logger.error(f"信息验证失败: {err}")
            await handler.comment_issue(await render_error(err))
            await remove_check_matcher.finish()

        title = f"{result.publish_type}: Remove {result.name or 'Unknown'}"[
            :TITLE_MAX_LENGTH
        ]
        branch_name = f"{BRANCH_NAME_PREFIX}{issue_number}"

        # 根据 input_config 里的 remove 仓库来进行提交和 PR
        # owner, repo = plugin_config.input_config.remove_repository.split("/")
        rm_handler = GithubHandler(
            bot=handler.bot, repo_info=plugin_config.input_config.remove_repository
        )
        # 处理拉取请求和议题标题
        await process_pull_reqeusts(handler, rm_handler, result, branch_name, title)

        await handler.update_issue_title(title)

        pull_number = (await rm_handler.get_pull_request_by_branch(branch_name)).number
        await handler.comment_issue(
            await render_comment(
                result,
                pr_url=f"{plugin_config.input_config.remove_repository}#{pull_number}",
            )
        )
