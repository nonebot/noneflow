import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pytest_mock import MockerFixture
from respx import MockRouter


async def test_validate_plugin(
    tmp_path: Path, mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """验证插件信息"""
    from src.utils.store_test.validation import StorePlugin, validate_plugin

    mock_datetime = mocker.patch("src.utils.store_test.validation.datetime")
    mock_datetime.now.return_value = datetime(
        2023, 8, 23, 9, 22, 14, 836035, tzinfo=ZoneInfo("Asia/Shanghai")
    )

    plugin_test_dir = tmp_path / "plugin_test"
    plugin_test_dir.mkdir()

    output_path = Path(__file__).parent / "output.txt"
    temp_output_path = plugin_test_dir / "output.txt"
    shutil.copyfile(output_path, temp_output_path)

    assert temp_output_path.exists()

    mock_plugin_test = mocker.MagicMock()
    mocker.patch(
        "src.utils.store_test.validation.PluginTest", return_value=mock_plugin_test
    )
    mock_run = mocker.AsyncMock()
    mock_run.return_value = (True, "output")
    mock_plugin_test.run = mock_run
    mock_plugin_test.path = plugin_test_dir

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author="author",
        tags=[],
        is_official=False,
    )

    result, new_plugin = await validate_plugin(plugin, "")

    assert result["version"] == "0.3.0"
    assert new_plugin == {
        "author": "author",
        "desc": "获取插件帮助信息",
        "homepage": "https://nonebot.dev/",
        "is_official": False,
        "module_name": "module_name",
        "name": "帮助",
        "project_link": "project_link",
        "supported_adapters": None,
        "tags": [],
        "time": "2023-08-23T09:22:14.836035+08:00",
        "type": "application",
        "valid": True,
        "version": "0.3.0",
    }

    assert mocked_api["homepage"].called

    assert not temp_output_path.exists()
    assert not plugin_test_dir.exists()
