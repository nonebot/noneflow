from pathlib import Path
from typing import cast

from nonebot.adapters.github import (
    Adapter,
    Event,
    IssueCommentCreated,
    IssuesOpened,
    PullRequestClosed,
    PullRequestReviewSubmitted,
)

# 事件类型对应的事件名称和事件文件名
EVENT_INFO = {
    IssuesOpened: ("issues", "issue-open"),
    IssueCommentCreated: ("issue_comment", "issue-comment"),
    PullRequestClosed: ("pull_request", "pr-close"),
    PullRequestReviewSubmitted: (
        "pull_request_review",
        "pull_request_review_submitted",
    ),
}


def get_mock_event[T: Event](
    event_type: type[T], filename: str = "", id: str = "1"
) -> T:
    """通过事件类型获取事件对象"""

    if event_type not in EVENT_INFO:
        raise ValueError(f"Unknown event type: {event_type}")

    event_name, event_filename = EVENT_INFO[event_type]
    if filename:
        event_filename = filename

    event_path = Path(__file__).parent / "events" / f"{event_filename}.json"
    event = Adapter.payload_to_event(id, event_name, event_path.read_bytes())

    assert isinstance(event, event_type)
    return cast("T", event)
