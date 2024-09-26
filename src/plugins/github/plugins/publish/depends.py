from githubkit.rest import (
    PullRequestPropLabelsItems,
    PullRequestSimple,
    WebhookIssueCommentCreatedPropIssueAllof0PropLabelsItems,
    WebhookIssuesEditedPropIssuePropLabelsItems,
    WebhookIssuesOpenedPropIssuePropLabelsItems,
    WebhookIssuesReopenedPropIssueMergedLabels,
    WebhookPullRequestReviewSubmittedPropPullRequestPropLabelsItems,
)
from githubkit.typing import Missing
from nonebot.adapters.github import Bot

from nonebot.params import Depends

from src.plugins.github.depends import get_issue_title, get_labels, get_repo_info
from src.plugins.github.plugins.publish import utils
from src.providers.validation.models import PublishType
from src.plugins.github.models import RepoInfo


def get_type_by_labels(
    labels: list[PullRequestPropLabelsItems]
    | list[WebhookPullRequestReviewSubmittedPropPullRequestPropLabelsItems]
    | Missing[list[WebhookIssuesOpenedPropIssuePropLabelsItems]]
    | Missing[list[WebhookIssuesReopenedPropIssueMergedLabels]]
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
