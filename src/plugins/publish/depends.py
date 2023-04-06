from githubkit.rest.models import IssuePropLabelsItemsOneof1, Label, PullRequestSimple
from githubkit.webhooks.models import Label as WebhookLabel
from nonebot import logger
from nonebot.adapters.github import (
    GitHubBot,
    IssueCommentCreated,
    IssuesEdited,
    IssuesOpened,
    IssuesReopened,
    PullRequestClosed,
)
from nonebot.params import Depends

from . import utils
from .constants import COMMIT_MESSAGE_PREFIX
from .models import PublishType, RepoInfo


def get_repo_info(event: PullRequestClosed) -> RepoInfo:
    """获取仓库信息"""
    repo = event.payload.repository
    return RepoInfo(owner=repo.owner.login, name=repo.name)


def get_labels(event: PullRequestClosed) -> list["WebhookLabel"]:
    """获取标签"""
    labels = event.payload.pull_request.labels
    return labels


def get_type_by_labels(
    labels: list[Label]
    | list[WebhookLabel]
    | list[str | IssuePropLabelsItemsOneof1] = Depends(get_labels),
) -> PublishType | None:
    """通过标签获取类型"""
    return utils.get_type_by_labels(labels)


def get_pull_requests_by_label(
    bot: GitHubBot,
    repo_info: RepoInfo = Depends(get_repo_info),
    publish_type: PublishType = Depends(get_type_by_labels),
) -> list[PullRequestSimple]:
    pulls = bot.rest.pulls.list(**repo_info.dict(), state="open").parsed_data
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
