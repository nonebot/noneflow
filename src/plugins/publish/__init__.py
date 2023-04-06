from typing import TYPE_CHECKING

from nonebot import logger, on
from nonebot.adapters.github import GitHubBot, PullRequestClosed
from nonebot.params import Depends

from .config import plugin_config
from .depends import get_pull_requests_by_label, get_repo_info, get_type_by_labels
from .models import PublishType, RepoInfo
from .utils import (
    commit_and_push,
    extract_issue_number_from_ref,
    extract_publish_info_from_issue,
    run_shell_command,
)
from .validation import PublishInfo

if TYPE_CHECKING:
    from githubkit.rest.models import PullRequestSimple


async def related_to_pr(
    event: PullRequestClosed,
    publish_type: PublishType = Depends(get_type_by_labels),
) -> bool:
    return True


pr_close = on(rule=related_to_pr)


@pr_close.handle()
async def _(
    bot: GitHubBot,
    event: PullRequestClosed,
    publish_type: PublishType = Depends(get_type_by_labels),
    repo_info: RepoInfo = Depends(get_repo_info),
):
    ref = event.payload.pull_request.head.ref
    related_issue_number = extract_issue_number_from_ref(ref)
    if not related_issue_number:
        logger.error("无法获取相关的议题编号")
        return

    issue = bot.rest.issues.get(
        **repo_info.dict(), issue_number=related_issue_number
    ).parsed_data
    if issue.state == "open":
        logger.info(f"正在关闭议题 #{related_issue_number}")
        bot.rest.issues.update(
            **repo_info.dict(),
            issue_number=related_issue_number,
            state="closed",
            state_reason="completed"
            if event.payload.pull_request.merged
            else "not_planned",
        )
    logger.info(f"议题 #{related_issue_number} 已关闭")

    try:
        run_shell_command(["git", "push", "origin", "--delete", ref])
        logger.info(f"已删除对应分支")
    except:
        logger.info("对应分支不存在或已删除")

    if event.payload.pull_request.merged:
        logger.info("发布的拉取请求已合并，准备更新拉取请求的提交")
        pull_requests = get_pull_requests_by_label(bot, repo_info, publish_type)
        resolve_conflict_pull_requests(bot, repo_info, pull_requests)
    else:
        logger.info("发布的拉取请求未合并，已跳过")


def resolve_conflict_pull_requests(
    bot: GitHubBot,
    repo_info: RepoInfo,
    pulls: list["PullRequestSimple"],
):
    """根据关联的议题提交来解决冲突

    参考对应的议题重新更新对应分支
    """
    # 跳过插件测试，因为这个时候插件测试任务没有运行
    plugin_config.skip_plugin_test = True

    for pull in pulls:
        # 回到主分支
        run_shell_command(["git", "checkout", plugin_config.input_config.base])
        # 切换到对应分支
        run_shell_command(["git", "switch", "-C", pull.head.ref])

        issue_number = extract_issue_number_from_ref(pull.head.ref)
        if not issue_number:
            logger.error(f"无法获取 {pull.title} 对应的议题")
            return

        logger.info(f"正在处理 {pull.title}")
        issue = bot.rest.issues.get(
            **repo_info.dict(), issue_number=issue_number
        ).parsed_data

        publish_type = get_type_by_labels(issue.labels)
        if publish_type:
            info = extract_publish_info_from_issue(issue, publish_type)
            if isinstance(info, PublishInfo):
                info.update_file()
                commit_and_push(info, pull.head.ref, issue_number)
                logger.info("拉取请求更新完毕")
            else:
                logger.info(info.message)
                logger.info("发布没通过检查，已跳过")
