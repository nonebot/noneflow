# ruff: noqa: UP040
from typing import TypeAlias

from githubkit.rest import (
    PullRequestPropLabelsItems,
    PullRequestSimplePropLabelsItems,
    WebhookIssueCommentCreatedPropIssueAllof0PropLabelsItems,
    WebhookIssuesEditedPropIssuePropLabelsItems,
    WebhookIssuesOpenedPropIssuePropLabelsItems,
    WebhookIssuesReopenedPropIssuePropLabelsItems,
    WebhookPullRequestReviewSubmittedPropPullRequestPropLabelsItems,
)
from githubkit.typing import Missing
from nonebot.adapters.github import (
    IssueCommentCreated,
    IssuesEdited,
    IssuesOpened,
    IssuesReopened,
    PullRequestClosed,
    PullRequestReviewSubmitted,
)

IssuesEvent: TypeAlias = (
    IssuesOpened | IssuesReopened | IssuesEdited | IssueCommentCreated
)

PullRequestEvent: TypeAlias = PullRequestClosed | PullRequestReviewSubmitted


PullRequestLabels: TypeAlias = (
    list[PullRequestSimplePropLabelsItems]
    | list[PullRequestPropLabelsItems]
    | list[WebhookPullRequestReviewSubmittedPropPullRequestPropLabelsItems]
)

IssueLabels: TypeAlias = (
    Missing[list[WebhookIssuesOpenedPropIssuePropLabelsItems]]
    | Missing[list[WebhookIssuesReopenedPropIssuePropLabelsItems]]
    | Missing[list[WebhookIssuesEditedPropIssuePropLabelsItems]]
    | list[WebhookIssueCommentCreatedPropIssueAllof0PropLabelsItems]
)

LabelsItems: TypeAlias = PullRequestLabels | IssueLabels
