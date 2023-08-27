import json
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

    assert result == {
        "time": "2023-08-23T09:22:14.836035+08:00",
        "version": "0.3.0",
        "inputs": {"config": ""},
        "results": {
            "load": True,
            "metadata": True,
            "validation": True,
        },
        "outputs": {
            "load": "output",
            "metadata": {
                "name": "帮助",
                "description": "获取插件帮助信息",
                "usage": "获取插件列表\n/help\n获取插件树\n/help -t\n/help --tree\n获取某个插件的帮助\n/help 插件名\n获取某个插件的树\n/help --tree 插件名\n",
                "type": "application",
                "homepage": "https://nonebot.dev/",
                "supported_adapters": None,
            },
            "validation": None,
        },
    }
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
        "skip_plugin_test": False,
    }

    assert mocked_api["homepage"].called

    assert not temp_output_path.exists()
    assert not plugin_test_dir.exists()


async def test_validate_plugin_with_data(
    mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """验证插件信息，提供数据的情况

    应该不会调用 API，直接使用传递进来的数据，并且 metadata 会缺少 usage（因为拉取请求关闭时无法获取，所以并没有传递过来）。
    """
    from src.utils.store_test.validation import StorePlugin, validate_plugin

    mock_datetime = mocker.patch("src.utils.store_test.validation.datetime")
    mock_datetime.now.return_value = datetime(
        2023, 8, 23, 9, 22, 14, 836035, tzinfo=ZoneInfo("Asia/Shanghai")
    )

    mocked_plugin_test = mocker.patch("src.utils.store_test.validation.PluginTest")

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author="author",
        tags=[],
        is_official=False,
    )

    data = {
        "project_link": "project_link",
        "module_name": "module_name",
        "author": "author",
        "name": "帮助",
        "desc": "获取插件帮助信息",
        "homepage": "https://nonebot.dev/",
        "is_official": False,
        "tags": [],
        "type": "application",
        "supported_adapters": None,
    }

    result, new_plugin = await validate_plugin(plugin, "", json.dumps(data))

    assert result == {
        "time": "2023-08-23T09:22:14.836035+08:00",
        "version": None,
        "inputs": {"config": ""},
        "results": {
            "load": True,
            "metadata": True,
            "validation": True,
        },
        "outputs": {
            "load": "已跳过测试",
            "metadata": {
                "name": "帮助",
                "description": "获取插件帮助信息",
                "type": "application",
                "homepage": "https://nonebot.dev/",
                "supported_adapters": None,
            },
            "validation": None,
        },
    }
    assert new_plugin == {
        "project_link": "project_link",
        "module_name": "module_name",
        "tags": [],
        "name": "帮助",
        "desc": "获取插件帮助信息",
        "author": "author",
        "homepage": "https://nonebot.dev/",
        "is_official": False,
        "supported_adapters": None,
        "type": "application",
        "time": "2023-08-23T09:22:14.836035+08:00",
        "valid": True,
        "version": None,
        "skip_plugin_test": True,
    }

    assert not mocked_api["homepage"].called

    mocked_plugin_test.assert_not_called()
