from typing import TypeAlias
from nonebot.adapters.github import (
    IssueCommentCreated,
    IssuesEdited,
    IssuesOpened,
    IssuesReopened,
    PullRequestClosed,
    PullRequestReviewSubmitted,
)

# 暂不用 type 关键字，编辑器不支持
IssuesEvent: TypeAlias = (
    IssuesOpened | IssuesReopened | IssuesEdited | IssueCommentCreated
)
PullRequestEvent: TypeAlias = PullRequestClosed | PullRequestReviewSubmitted
