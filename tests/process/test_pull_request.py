# type: ignore
import json
from pathlib import Path

from github.Repository import Repository
from pytest_mock import MockerFixture

from src.models import Config, Settings
from src.process import process_pull_request_event


def test_process_pull_request(mocker: MockerFixture, tmp_path: Path) -> None:
    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_get_pull_requests_by_label = mocker.patch(
        "src.process.get_pull_requests_by_label"
    )
    mock_resolve_conflict_pull_requests = mocker.patch(
        "src.process.resolve_conflict_pull_requests"
    )
    mock_repo: Repository = mocker.MagicMock()

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"
    mock_repo.get_pull().labels = [mock_label]
    mock_repo.get_pull().head.ref = "publish/issue1"
    mock_repo.get_pull().merged = True

    with open(tmp_path / "event.json", "w") as f:
        json.dump(
            {
                "action": "closed",
                "pull_request": {
                    "number": 2,
                },
            },
            f,
        )

    mock_settings: Settings = mocker.MagicMock()
    mock_settings.github_event_path = str(tmp_path / "event.json")
    mock_settings.input_config = Config(
        base="master",
        plugin_path=tmp_path / "plugin.json",
        bot_path=tmp_path / "bot.json",
        adapter_path=tmp_path / "adapter.json",
    )

    process_pull_request_event(mock_settings, mock_repo)

    mock_repo.get_pull.assert_called_with(2)
    mock_repo.get_issue.assert_called_with(1)

    # 测试 git 命令
    mock_subprocess_run.assert_called_once_with(
        ["git", "push", "origin", "--delete", "publish/issue1"], check=True
    )

    mock_get_pull_requests_by_label.assert_called_once_with(mock_repo, "Bot")
    mock_resolve_conflict_pull_requests.assert_called_once()