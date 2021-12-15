# type: ignore
from github.Issue import Issue
from pytest_mock import MockerFixture

from src.utils import comment_issue


def test_comment_issue(mocker: MockerFixture):
    mock_issue: Issue = mocker.MagicMock()  # type: ignore
    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_issue.get_comments.return_value = [mock_comment]

    comment_issue(mock_issue, "test")

    mock_comment.edit.assert_not_called()
    mock_issue.create_comment.assert_called_once_with(
        "# 📃 Publish Check Result\n\ntest\n\n---\n\n💪 Powered by NoneBot2 Publish Bot\n"
    )


def test_comment_issue_reuse(mocker: MockerFixture):
    mock_issue: Issue = mocker.MagicMock()  # type: ignore
    mock_comment = mocker.MagicMock()
    mock_comment.body = "# 📃 Publish Check Result"
    mock_issue.get_comments.return_value = [mock_comment]

    comment_issue(mock_issue, "test")

    mock_issue.create_comment.assert_not_called()
    mock_comment.edit.assert_called_once_with(
        "# 📃 Publish Check Result\n\ntest\n\n---\n\n♻️ This comment has been updated with the latest result.\n\n💪 Powered by NoneBot2 Publish Bot\n"
    )
