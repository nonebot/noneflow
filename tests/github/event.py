from pathlib import Path
from typing import TypeVar

from nonebot.adapters.github import (
    Adapter,
    Event,
    IssueCommentCreated,
    IssuesOpened,
    PullRequestClosed,
    PullRequestReviewSubmitted,
)

T = TypeVar("T", bound=Event)

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


def get_mock_event(event_type: type[T], filename: str = "", id: str = "1") -> T:
    """通过事件类型获取事件对象"""

    if event_type not in EVENT_INFO:
        raise ValueError(f"Unknown event type: {event_type}")

    event_name, _filename = EVENT_INFO[event_type]
    if filename:
        _filename = filename

    event_path = Path(__file__).parent / "events" / f"{_filename}.json"
    event = Adapter.payload_to_event(id, event_name, event_path.read_bytes())

    assert isinstance(event, event_type)
    return event
