from collections.abc import AsyncGenerator

from githubkit.rest.models import IssuePropLabelsItemsOneof1, Label, PullRequestSimple
from githubkit.webhooks.models import Label as WebhookLabel
from nonebot.adapters.github import (
    Bot,
    GitHubBot,
    IssueCommentCreated,
    IssuesEdited,
    IssuesOpened,
    IssuesReopened,
    PullRequestClosed,
)
from nonebot.params import Depends

from . import utils
from .models import PublishType, RepoInfo


def get_repo_info(
    event: PullRequestClosed
    | IssuesOpened
    | IssuesReopened
    | IssuesEdited
    | IssueCommentCreated,
) -> RepoInfo:
    """获取仓库信息"""
    repo = event.payload.repository
    return RepoInfo(owner=repo.owner.login, repo=repo.name)


def get_labels(
    event: PullRequestClosed
    | IssuesOpened
    | IssuesReopened
    | IssuesEdited
    | IssueCommentCreated,
):
    """获取标签"""
    if isinstance(event, PullRequestClosed):
        labels = event.payload.pull_request.labels
    else:
        labels = event.payload.issue.labels
    return labels


def get_type_by_labels(
    labels: list[Label]
    | list[WebhookLabel]
    | list[str | IssuePropLabelsItemsOneof1] = Depends(get_labels),
) -> PublishType | None:
    """通过标签获取类型"""
    return utils.get_type_by_labels(labels)


async def get_pull_requests_by_label(
    bot: Bot,
    repo_info: RepoInfo = Depends(get_repo_info),
    publish_type: PublishType = Depends(get_type_by_labels),
) -> list[PullRequestSimple]:
    pulls = (
        await bot.rest.pulls.async_list(**repo_info.dict(), state="open")
    ).parsed_data
    return [
        pull
        for pull in pulls
        if publish_type.value in [label.name for label in pull.labels]
    ]


def get_issue_number(
    event: IssuesOpened | IssuesReopened | IssuesEdited | IssueCommentCreated,
) -> int:
    """获取议题编号"""
    return event.payload.issue.number


async def get_installed_bot(
    bot: GitHubBot,
    repo_info: RepoInfo = Depends(get_repo_info),
) -> AsyncGenerator[GitHubBot, None]:
    """获取安装后的 Bot"""
    installation = (
        await bot.rest.apps.async_get_repo_installation(**repo_info.dict())
    ).parsed_data
    async with bot.as_installation(installation.id):
        yield bot
