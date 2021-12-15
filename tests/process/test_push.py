# type: ignore
import json
from pathlib import Path

from github.Repository import Repository
from pytest_mock import MockerFixture

from src.models import Config, Settings
from src.process import process_push_event


def test_process_push(mocker: MockerFixture, tmp_path: Path) -> None:
    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_get_pull_requests_by_label = mocker.patch(
        "src.process.get_pull_requests_by_label"
    )
    mock_resolve_conflict_pull_requests = mocker.patch(
        "src.process.resolve_conflict_pull_requests"
    )
    mock_repo: Repository = mocker.MagicMock()

    with open(tmp_path / "event.json", "w") as f:
        json.dump(
            {
                "head_commit": {
                    "message": ":beers: publish bot test",
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

    process_push_event(mock_settings, mock_repo)

    mock_get_pull_requests_by_label.assert_called_once_with(mock_repo, "Bot")
    mock_resolve_conflict_pull_requests.assert_called_once()
