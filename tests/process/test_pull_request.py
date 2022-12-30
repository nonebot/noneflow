from pathlib import Path

from pytest_mock import MockerFixture


def test_process_pull_request(mocker: MockerFixture, tmp_path: Path) -> None:
    from src import Bot

    bot = Bot()
    bot.github = mocker.MagicMock()

    mock_subprocess_run = mocker.patch("subprocess.run")
    bot.get_pull_requests_by_label = mocker.MagicMock()
    bot.get_pull_requests_by_label.return_value = []
    bot.resolve_conflict_pull_requests = mocker.MagicMock()

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"

    mock_event = mocker.MagicMock()
    mock_event.pull_request.labels = [mock_label]
    mock_event.pull_request.head.ref = "publish/issue1"
    mock_event.pull_request.merged = True

    mock_issues_resp = mocker.MagicMock()
    bot.github.rest.issues.get.return_value = mock_issues_resp
    mock_issue = mocker.MagicMock()
    mock_issue.state = "open"
    mock_issues_resp.parsed_data = mock_issue

    bot.process_pull_request_event(mock_event)

    bot.github.rest.issues.get.assert_called_once_with("owner", "repo", 1)

    bot.github.rest.issues.update.assert_called_once_with(
        "owner", "repo", 1, state="closed", state_reason="completed"
    )

    # 测试 git 命令
    mock_subprocess_run.assert_called_once_with(
        ["git", "push", "origin", "--delete", "publish/issue1"],
        check=True,
        capture_output=True,
    )

    # 处理冲突的拉取请求
    bot.get_pull_requests_by_label.assert_called_once_with("Bot")
    bot.resolve_conflict_pull_requests.assert_called_once_with([])


def test_process_pull_request_not_merged(mocker: MockerFixture, tmp_path: Path) -> None:
    from src import Bot

    bot = Bot()
    bot.github = mocker.MagicMock()

    mock_subprocess_run = mocker.patch("subprocess.run")
    bot.get_pull_requests_by_label = mocker.MagicMock()
    bot.get_pull_requests_by_label.return_value = []
    bot.resolve_conflict_pull_requests = mocker.MagicMock()

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"

    mock_event = mocker.MagicMock()
    mock_event.pull_request.labels = [mock_label]
    mock_event.pull_request.head.ref = "publish/issue1"
    mock_event.pull_request.merged = False

    mock_issues_resp = mocker.MagicMock()
    bot.github.rest.issues.get.return_value = mock_issues_resp
    mock_issue = mocker.MagicMock()
    mock_issue.state = "open"
    mock_issues_resp.parsed_data = mock_issue

    bot.process_pull_request_event(mock_event)

    bot.github.rest.issues.get.assert_called_once_with("owner", "repo", 1)

    bot.github.rest.issues.update.assert_called_once_with(
        "owner", "repo", 1, state="closed", state_reason="not_planned"
    )

    # 测试 git 命令
    mock_subprocess_run.assert_called_once_with(
        ["git", "push", "origin", "--delete", "publish/issue1"],
        check=True,
        capture_output=True,
    )

    # 处理冲突的拉取请求
    bot.get_pull_requests_by_label.assert_not_called()
    bot.resolve_conflict_pull_requests.assert_not_called()
