from githubkit.rest import (
    PullRequestPropLabelsItems,
    PullRequestSimple,
    WebhookIssueCommentCreatedPropIssueAllof0PropLabelsItems,
    WebhookIssuesEditedPropIssuePropLabelsItems,
    WebhookIssuesOpenedPropIssuePropLabelsItems,
    WebhookIssuesReopenedPropIssuePropLabelsItems,
    WebhookPullRequestReviewSubmittedPropPullRequestPropLabelsItems,
)
from githubkit.typing import Missing
from nonebot.adapters.github import (
    Bot,
    GitHubBot,
    IssueCommentCreated,
    IssuesEdited,
    IssuesOpened,
    IssuesReopened,
    PullRequestClosed,
    PullRequestReviewSubmitted,
)
from nonebot.params import Depends

from src.utils.validation.models import PublishType

from . import utils
from .models import RepoInfo


def get_repo_info(
    event: PullRequestClosed
    | PullRequestReviewSubmitted
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
    | PullRequestReviewSubmitted
    | IssuesOpened
    | IssuesReopened
    | IssuesEdited
    | IssueCommentCreated,
):
    """获取议题或拉取请求的标签"""
    if isinstance(event, PullRequestClosed | PullRequestReviewSubmitted):
        labels = event.payload.pull_request.labels
    else:
        labels = event.payload.issue.labels
    return labels


def get_issue_title(
    event: IssuesOpened | IssuesReopened | IssuesEdited | IssueCommentCreated,
):
    """获取议题标题"""
    return event.payload.issue.title


def get_type_by_labels(
    labels: list[PullRequestPropLabelsItems]
    | list[WebhookPullRequestReviewSubmittedPropPullRequestPropLabelsItems]
    | Missing[list[WebhookIssuesOpenedPropIssuePropLabelsItems]]
    | Missing[list[WebhookIssuesReopenedPropIssuePropLabelsItems]]
    | Missing[list[WebhookIssuesEditedPropIssuePropLabelsItems]]
    | list[WebhookIssueCommentCreatedPropIssueAllof0PropLabelsItems] = Depends(
        get_labels
    ),
) -> PublishType | None:
    """通过标签获取类型"""
    return utils.get_type_by_labels(labels)


def get_type_by_title(title: str = Depends(get_issue_title)) -> PublishType | None:
    """通过标题获取类型"""
    return utils.get_type_by_title(title)


async def get_pull_requests_by_label(
    bot: Bot,
    repo_info: RepoInfo = Depends(get_repo_info),
    publish_type: PublishType = Depends(get_type_by_labels),
) -> list[PullRequestSimple]:
    pulls = (
        await bot.rest.pulls.async_list(**repo_info.model_dump(), state="open")
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


async def get_installation_id(
    bot: GitHubBot,
    repo_info: RepoInfo = Depends(get_repo_info),
) -> int:
    """获取 GitHub App 的 Installation ID"""
    installation = (
        await bot.rest.apps.async_get_repo_installation(**repo_info.model_dump())
    ).parsed_data
    return installation.id


def get_related_issue_number(event: PullRequestClosed) -> int | None:
    ref = event.payload.pull_request.head.ref
    related_issue_number = utils.extract_issue_number_from_ref(ref)
    return related_issue_number
