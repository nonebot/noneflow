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
        is_official=True,
    )

    result, new_plugin = await validate_plugin(plugin, "", False)

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
        "is_official": True,
        "module_name": "module_name",
        "name": "帮助",
        "project_link": "project_link",
        "supported_adapters": None,
        "tags": [],
        "time": "2023-09-01T00:00:00+00:00Z",
        "type": "application",
        "valid": True,
        "version": "0.3.0",
        "skip_test": False,
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

    result, new_plugin = await validate_plugin(plugin, "", False, json.dumps(data))

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
        "time": "2023-09-01T00:00:00+00:00Z",
        "valid": True,
        "version": "0.0.1",
        "skip_test": True,
    }

    assert not mocked_api["homepage"].called

    mocked_plugin_test.assert_not_called()


async def test_validate_plugin_skip_test(
    tmp_path: Path, mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """跳过插件测试的情况

    如果插件之前是跳过测试的，如果插件测试成功，应将 skip_test 设置为 False。
    """
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

    result, new_plugin = await validate_plugin(plugin, "", True)

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
        "time": "2023-09-01T00:00:00+00:00Z",
        "type": "application",
        "valid": True,
        "version": "0.3.0",
        "skip_test": False,
    }

    assert mocked_api["homepage"].called

    assert not temp_output_path.exists()
    assert not plugin_test_dir.exists()


async def test_validate_plugin_skip_test_plugin_test_failed(
    tmp_path: Path, mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """跳过插件测试的情况

    如果插件之前是跳过测试的，如果插件测试失败，应不改变 skip_test 的值。
    """
    from src.utils.store_test.validation import StorePlugin, validate_plugin

    mock_datetime = mocker.patch("src.utils.store_test.validation.datetime")
    mock_datetime.now.return_value = datetime(
        2023, 8, 23, 9, 22, 14, 836035, tzinfo=ZoneInfo("Asia/Shanghai")
    )

    plugin_test_dir = tmp_path / "plugin_test"
    plugin_test_dir.mkdir()

    output_path = Path(__file__).parent / "output_failed.txt"
    temp_output_path = plugin_test_dir / "output.txt"
    shutil.copyfile(output_path, temp_output_path)

    assert temp_output_path.exists()

    mock_plugin_test = mocker.MagicMock()
    mocker.patch(
        "src.utils.store_test.validation.PluginTest", return_value=mock_plugin_test
    )
    mock_run = mocker.AsyncMock()
    mock_run.return_value = (False, "output")
    mock_plugin_test.run = mock_run
    mock_plugin_test.path = plugin_test_dir

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author="author",
        tags=[],
        is_official=False,
    )

    result, new_plugin = await validate_plugin(
        plugin,
        "",
        True,
        previous_plugin={
            "module_name": "nonebot_plugin_treehelp",
            "project_link": "nonebot-plugin-treehelp",
            "name": "帮助",
            "desc": "获取插件帮助信息",
            "author": "he0119",
            "homepage": "https://nonebot.dev/",
            "tags": [],
            "is_official": False,
            "type": "application",
            "supported_adapters": None,
            "valid": True,
            "time": "2023-06-22 12:10:18",
            "version": "0.3.0",
            "skip_test": True,
        },
    )

    assert result == {
        "time": "2023-08-23T09:22:14.836035+08:00",
        "version": "0.3.0",
        "inputs": {"config": ""},
        "results": {
            "load": False,
            "metadata": False,
            "validation": True,
        },
        "outputs": {
            "load": "output",
            "metadata": None,
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
        "time": "2023-09-01T00:00:00+00:00Z",
        "type": "application",
        "valid": True,
        "version": "0.3.0",
        "skip_test": True,
    }

    assert mocked_api["homepage"].called

    assert not temp_output_path.exists()
    assert not plugin_test_dir.exists()


async def test_validate_plugin_failed(
    tmp_path: Path, mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """插件验证失败的情况"""
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
    mock_run.return_value = (False, "output")
    mock_plugin_test.run = mock_run
    mock_plugin_test.path = plugin_test_dir

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author="author",
        tags=[],
        is_official=False,
    )

    result, new_plugin = await validate_plugin(plugin, "", False)

    assert result == {
        "time": "2023-08-23T09:22:14.836035+08:00",
        "version": "0.3.0",
        "inputs": {"config": ""},
        "results": {
            "load": False,
            "metadata": True,
            "validation": False,
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
            "validation": {
                "data": {
                    "module_name": "module_name",
                    "project_link": "project_link",
                    "name": "帮助",
                    "desc": "获取插件帮助信息",
                    "author": "author",
                    "homepage": "https://nonebot.dev/",
                    "tags": [],
                    "is_official": False,
                    "type": "application",
                    "supported_adapters": None,
                },
                "errors": [
                    {
                        "loc": ("plugin_test",),
                        "msg": "插件无法正常加载",
                        "type": "value_error.plugin_test",
                        "ctx": {"output": ""},
                    }
                ],
            },
        },
    }
    assert new_plugin is None

    assert mocked_api["homepage"].called

    assert not temp_output_path.exists()
    assert not plugin_test_dir.exists()
