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
from nonebot.params import Arg, Depends
from nonebot.rule import Rule
from nonebot.typing import T_State

from src.plugins.github.constants import (
    BRANCH_NAME_PREFIX,
    TITLE_MAX_LENGTH,
)
from src.plugins.github.depends import (
    bypass_git,
    get_github_handler,
    get_installation_id,
    get_issue_handler,
    get_related_issue_handler,
    get_related_issue_number,
    install_pre_commit_hooks,
    is_bot_triggered_workflow,
    is_publish_workflow,
)
from src.plugins.github.models import GithubHandler, IssueHandler
from src.providers.validation.models import PublishType, ValidationDict

from .depends import (
    get_type_by_labels_name,
)
from .render import render_comment
from .utils import (
    ensure_issue_content,
    ensure_issue_plugin_test_button,
    ensure_issue_plugin_test_button_in_progress,
    process_pull_request,
    trigger_registry_update,
)
from .validation import (
    validate_adapter_info_from_issue,
    validate_bot_info_from_issue,
    validate_plugin_info_from_issue,
)


async def check_rule(
    event: IssuesOpened | IssuesReopened | IssuesEdited | IssueCommentCreated,
    is_bot: bool = Depends(is_bot_triggered_workflow),
    is_publish: bool = Depends(is_publish_workflow),
) -> bool:
    if is_bot:
        logger.info("机器人触发的工作流，已跳过")
        return False
    if event.payload.issue.pull_request:
        logger.info("评论在拉取请求下，已跳过")
        return False
    if not is_publish:
        logger.info("议题与发布无关，已跳过")
        return False

    return True


publish_check_matcher = on_type(
    (IssuesOpened, IssuesReopened, IssuesEdited, IssueCommentCreated),
    rule=Rule(check_rule),
)


@publish_check_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_publish_plugin_check(
    bot: GitHubBot,
    state: T_State,
    installation_id: int = Depends(get_installation_id),
    handler: IssueHandler = Depends(get_issue_handler),
    publish_type: Literal[PublishType.PLUGIN] = Depends(get_type_by_labels_name),
) -> None:
    async with bot.as_installation(installation_id):
        if handler.issue.state != "open":
            logger.info("议题未开启，已跳过")
            await publish_check_matcher.finish()

        # 提示插件正在测试中
        await ensure_issue_plugin_test_button_in_progress(handler)

        # 是否需要跳过插件测试
        skip_test = await handler.should_skip_test()
        # 如果需要跳过插件测试，则修改议题内容，确保其包含插件所需信息
        if skip_test:
            await ensure_issue_content(handler)

        # 检查是否满足发布要求
        # 仅在通过检查的情况下创建拉取请求
        result = await validate_plugin_info_from_issue(handler, skip_test)

        # 确保插件重测按钮存在
        await ensure_issue_plugin_test_button(handler)

        state["validation"] = result


@publish_check_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_adapter_publish_check(
    bot: GitHubBot,
    state: T_State,
    installation_id: int = Depends(get_installation_id),
    handler: IssueHandler = Depends(get_issue_handler),
    publish_type: Literal[PublishType.ADAPTER] = Depends(get_type_by_labels_name),
) -> None:
    async with bot.as_installation(installation_id):
        if handler.issue.state != "open":
            logger.info("议题未开启，已跳过")
            await publish_check_matcher.finish()

        # 检查是否满足发布要求
        # 仅在通过检查的情况下创建拉取请求
        result = await validate_adapter_info_from_issue(handler.issue)

        state["validation"] = result


@publish_check_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_bot_publish_check(
    bot: GitHubBot,
    state: T_State,
    installation_id: int = Depends(get_installation_id),
    handler: IssueHandler = Depends(get_issue_handler),
    publish_type: Literal[PublishType.BOT] = Depends(get_type_by_labels_name),
) -> None:
    async with bot.as_installation(installation_id):
        if handler.issue.state != "open":
            logger.info("议题未开启，已跳过")
            await publish_check_matcher.finish()

        # 检查是否满足发布要求
        # 仅在通过检查的情况下创建拉取请求
        result = await validate_bot_info_from_issue(handler.issue)

        state["validation"] = result


@publish_check_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_pull_request_and_update_issue(
    bot: GitHubBot,
    validation: ValidationDict = Arg(),
    handler: IssueHandler = Depends(get_issue_handler),
    installation_id: int = Depends(get_installation_id),
) -> None:
    async with bot.as_installation(installation_id):
        # 渲染评论信息
        comment = await render_comment(validation, True)

        # 对议题评论
        await handler.comment_issue(comment)

        # 设置拉取请求与议题的标题
        # 限制标题长度，过长的标题不好看
        title = f"{validation.type}: {validation.name[:TITLE_MAX_LENGTH]}"

        # 修改议题标题
        await handler.update_issue_title(title)

        branch_name = f"{BRANCH_NAME_PREFIX}{handler.issue_number}"

        # 验证之后创建拉取请求和修改议题的标题
        await process_pull_request(handler, validation, branch_name, title)


async def pr_close_rule(
    is_publish: bool = Depends(is_publish_workflow),
    related_issue_number: int | None = Depends(get_related_issue_number),
) -> bool:
    if not is_publish:
        logger.info("拉取请求与发布无关，已跳过")
        return False

    if not related_issue_number:
        logger.error("无法获取相关的议题编号")
        return False

    return True


pr_close_matcher = on_type(PullRequestClosed, rule=Rule(pr_close_rule))


@pr_close_matcher.handle(
    parameterless=[Depends(bypass_git), Depends(install_pre_commit_hooks)]
)
async def handle_pr_close(
    event: PullRequestClosed,
    bot: GitHubBot,
    installation_id: int = Depends(get_installation_id),
    publish_type: PublishType = Depends(get_type_by_labels_name),
    handler: IssueHandler = Depends(get_related_issue_handler),
) -> None:
    async with bot.as_installation(installation_id):
        # 如果商店更新则触发 registry 更新
        if event.payload.pull_request.merged:
            await trigger_registry_update(handler, publish_type)
        else:
            logger.info("拉取请求未合并，跳过触发商店列表更新")


async def review_submitted_rule(
    event: PullRequestReviewSubmitted,
    is_publish: bool = Depends(is_publish_workflow),
) -> bool:
    if not is_publish:
        logger.info("拉取请求与发布无关，已跳过")
        return False
    if event.payload.review.author_association not in ["OWNER", "MEMBER"]:
        logger.info("审查者不是仓库成员，已跳过")
        return False
    if event.payload.review.state != "approved":
        logger.info("未通过审查，已跳过")
        return False

    return True


auto_merge_matcher = on_type(
    PullRequestReviewSubmitted, rule=Rule(review_submitted_rule)
)


@auto_merge_matcher.handle(parameterless=[Depends(bypass_git)])
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
