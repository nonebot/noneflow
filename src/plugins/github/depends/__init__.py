from nonebot import logger
from nonebot.adapters.github import (
    GitHubBot,
    IssueCommentCreated,
    IssuesEdited,
    PullRequestClosed,
    PullRequestReviewSubmitted,
)
from nonebot.params import Depends

from src.plugins.github.models import GithubHandler, RepoInfo
from src.plugins.github.typing import IssuesEvent, LabelsItems, PullRequestEvent
from src.plugins.github.utils import run_shell_command

from .utils import extract_issue_number_from_ref


def bypass_git():
    """绕过检查"""
    # https://github.blog/2022-04-18-highlights-from-git-2-36/#stricter-repository-ownership-checks
    run_shell_command(["git", "config", "--global", "safe.directory", "*"])


def install_pre_commit_hooks():
    """安装 pre-commit 钩子"""
    run_shell_command(["pre-commit", "install", "--install-hooks"])


def get_labels(event: PullRequestEvent | IssuesEvent):
    """获取议题或拉取请求的标签"""
    if isinstance(event, PullRequestClosed | PullRequestReviewSubmitted):
        labels = event.payload.pull_request.labels
    else:
        labels = event.payload.issue.labels
    return labels


def get_issue_title(event: IssuesEvent):
    """获取议题标题"""
    return event.payload.issue.title


def get_repo_info(event: PullRequestEvent | IssuesEvent) -> RepoInfo:
    """获取仓库信息"""
    repo = event.payload.repository
    return RepoInfo(owner=repo.owner.login, repo=repo.name)


def get_name_by_labels(labels: LabelsItems = Depends(get_labels)) -> list[str]:
    """通过标签获取名称"""
    label_names: list[str] = []
    if not labels:
        return label_names

    for label in labels:
        if label.name:
            label_names.append(label.name)
    return label_names


async def get_installation_id(
    bot: GitHubBot, repo_info: RepoInfo = Depends(get_repo_info)
) -> int:
    """获取 GitHub App 的 Installation ID"""
    installation = (
        await bot.rest.apps.async_get_repo_installation(**repo_info.model_dump())
    ).parsed_data
    return installation.id


def get_issue_number(event: IssuesEvent) -> int:
    """获取议题编号"""
    return event.payload.issue.number


def get_related_issue_number(event: PullRequestClosed) -> int | None:
    """获取 PR 相关联的议题号"""
    ref = event.payload.pull_request.head.ref
    related_issue_number = extract_issue_number_from_ref(ref)
    return related_issue_number


def is_bot_triggered_workflow(event: IssuesEvent):
    """触发议题相关的工作流"""

    if (
        isinstance(event, IssueCommentCreated)
        and event.payload.comment.user
        and event.payload.comment.user.type == "Bot"
    ):
        logger.info("评论来自机器人，已跳过")
        return True
    if (
        isinstance(event, IssuesEdited)
        and event.payload.sender
        and event.payload.sender.type == "Bot"
    ):
        logger.info("议题修改来自机器人，已跳过")
        return True
    return False


def get_github_handler(bot: GitHubBot, repo_info: RepoInfo = Depends(get_repo_info)):
    """获取 GitHub 处理器"""
    return GithubHandler(bot=bot, repo_info=repo_info)
