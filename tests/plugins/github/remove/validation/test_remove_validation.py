"""测试 plugins/github/plugins/remove/validation.py"""

from pathlib import Path

import pytest
from inline_snapshot import snapshot
from nonebug import App
from pydantic_core import PydanticCustomError
from pytest_mock import MockerFixture

from tests.plugins.github.utils import (
    MockIssue,
    MockUser,
    generate_issue_body_remove,
)


async def test_load_publish_data_adapter(
    app: App, mocker: MockerFixture, tmp_path: Path
):
    """测试加载适配器数据"""
    from src.plugins.github import plugin_config
    from src.plugins.github.plugins.remove.validation import load_publish_data
    from src.providers.utils import dump_json5
    from src.providers.validation.models import PublishType

    adapters = [
        {
            "module_name": "nonebot.adapters.test",
            "project_link": "nonebot-adapter-test",
            "author_id": 1,
        }
    ]
    adapter_path = tmp_path / "adapters.json5"
    dump_json5(adapter_path, adapters)
    mocker.patch.object(plugin_config.input_config, "adapter_path", adapter_path)

    result = load_publish_data(PublishType.ADAPTER)

    assert result == snapshot(
        {
            "nonebot-adapter-test:nonebot.adapters.test": {
                "module_name": "nonebot.adapters.test",
                "project_link": "nonebot-adapter-test",
                "author_id": 1,
            }
        }
    )


async def test_load_publish_data_bot(app: App, mocker: MockerFixture, tmp_path: Path):
    """测试加载机器人数据"""
    from src.plugins.github import plugin_config
    from src.plugins.github.plugins.remove.validation import load_publish_data
    from src.providers.utils import dump_json5
    from src.providers.validation.models import PublishType

    bots = [
        {
            "name": "TestBot",
            "homepage": "https://nonebot.dev",
            "author_id": 1,
        }
    ]
    bot_path = tmp_path / "bots.json5"
    dump_json5(bot_path, bots)
    mocker.patch.object(plugin_config.input_config, "bot_path", bot_path)

    result = load_publish_data(PublishType.BOT)

    assert result == snapshot(
        {
            "TestBot:https://nonebot.dev": {
                "name": "TestBot",
                "homepage": "https://nonebot.dev",
                "author_id": 1,
            }
        }
    )


async def test_load_publish_data_plugin(
    app: App, mocker: MockerFixture, tmp_path: Path
):
    """测试加载插件数据"""
    from src.plugins.github import plugin_config
    from src.plugins.github.plugins.remove.validation import load_publish_data
    from src.providers.utils import dump_json5
    from src.providers.validation.models import PublishType

    plugins = [
        {
            "module_name": "nonebot_plugin_test",
            "project_link": "nonebot-plugin-test",
            "author_id": 1,
        }
    ]
    plugin_path = tmp_path / "plugins.json5"
    dump_json5(plugin_path, plugins)
    mocker.patch.object(plugin_config.input_config, "plugin_path", plugin_path)

    result = load_publish_data(PublishType.PLUGIN)

    assert result == snapshot(
        {
            "nonebot-plugin-test:nonebot_plugin_test": {
                "module_name": "nonebot_plugin_test",
                "project_link": "nonebot-plugin-test",
                "author_id": 1,
            }
        }
    )


async def test_load_publish_data_driver_raises(app: App):
    """测试加载驱动程序数据应该抛出异常"""
    from src.plugins.github.plugins.remove.validation import load_publish_data
    from src.providers.validation.models import PublishType

    with pytest.raises(ValueError, match="不支持的删除类型"):
        load_publish_data(PublishType.DRIVER)


async def test_validate_author_info_adapter(
    app: App, mocker: MockerFixture, tmp_path: Path
):
    """测试验证适配器作者信息"""
    from src.plugins.github import plugin_config
    from src.plugins.github.plugins.remove.validation import validate_author_info
    from src.providers.utils import dump_json5
    from src.providers.validation.models import PublishType

    adapters = [
        {
            "name": "Test Adapter",
            "module_name": "nonebot.adapters.test",
            "project_link": "nonebot-adapter-test",
            "author_id": 1,
        }
    ]
    adapter_path = tmp_path / "adapters.json5"
    dump_json5(adapter_path, adapters)
    mocker.patch.object(plugin_config.input_config, "adapter_path", adapter_path)

    mock_issue = MockIssue(
        body=generate_issue_body_remove(
            "Adapter", "nonebot-adapter-test:nonebot.adapters.test"
        ),
        user=MockUser(login="test", id=1),
    ).as_mock(mocker)

    result = await validate_author_info(mock_issue, PublishType.ADAPTER)

    assert result.publish_type == PublishType.ADAPTER
    assert result.key == "nonebot-adapter-test:nonebot.adapters.test"
    assert result.name == "Test Adapter"


async def test_validate_author_info_plugin_not_found(
    app: App, mocker: MockerFixture, tmp_path: Path
):
    """测试验证插件作者信息 - 插件未找到"""
    from src.plugins.github import plugin_config
    from src.plugins.github.plugins.remove.validation import validate_author_info
    from src.providers.utils import dump_json5
    from src.providers.validation.models import PublishType

    plugins: list = []
    plugin_path = tmp_path / "plugins.json5"
    dump_json5(plugin_path, plugins)
    mocker.patch.object(plugin_config.input_config, "plugin_path", plugin_path)

    mock_issue = MockIssue(
        body=generate_issue_body_remove("Plugin", "project_link:module_name"),
        user=MockUser(login="test", id=1),
    ).as_mock(mocker)

    with pytest.raises(PydanticCustomError) as exc_info:
        await validate_author_info(mock_issue, PublishType.PLUGIN)

    assert exc_info.value.type == "not_found"


async def test_validate_author_info_author_mismatch(
    app: App, mocker: MockerFixture, tmp_path: Path
):
    """测试验证作者信息 - 作者不匹配"""
    from src.plugins.github import plugin_config
    from src.plugins.github.plugins.remove.validation import validate_author_info
    from src.providers.utils import dump_json5
    from src.providers.validation.models import PublishType

    plugins = [
        {
            "name": "Test Plugin",
            "module_name": "module_name",
            "project_link": "project_link",
            "author_id": 999,  # 不同的作者 ID
        }
    ]
    plugin_path = tmp_path / "plugins.json5"
    dump_json5(plugin_path, plugins)
    mocker.patch.object(plugin_config.input_config, "plugin_path", plugin_path)

    mock_issue = MockIssue(
        body=generate_issue_body_remove("Plugin", "project_link:module_name"),
        user=MockUser(login="test", id=1),  # 当前用户 ID 为 1
    ).as_mock(mocker)

    with pytest.raises(PydanticCustomError) as exc_info:
        await validate_author_info(mock_issue, PublishType.PLUGIN)

    assert exc_info.value.type == "author_info"


async def test_validate_author_info_missing_info(
    app: App, mocker: MockerFixture, tmp_path: Path
):
    """测试验证作者信息 - 缺少必要信息"""
    from src.plugins.github.plugins.remove.validation import validate_author_info
    from src.providers.validation.models import PublishType

    # 创建一个没有完整信息的 issue body
    mock_issue = MockIssue(
        body="### PyPI 项目名\n\n\n\n### import 包名\n\n",  # 空的项目名和模块名
        user=MockUser(login="test", id=1),
    ).as_mock(mocker)

    with pytest.raises(PydanticCustomError) as exc_info:
        await validate_author_info(mock_issue, PublishType.PLUGIN)

    assert exc_info.value.type == "info_not_found"


async def test_validate_author_info_unsupported_type(
    app: App, mocker: MockerFixture, tmp_path: Path
):
    """测试验证作者信息 - 不支持的类型"""
    from src.plugins.github.plugins.remove.validation import validate_author_info
    from src.providers.validation.models import PublishType

    mock_issue = MockIssue(
        body="some content",
        user=MockUser(login="test", id=1),
    ).as_mock(mocker)

    with pytest.raises(PydanticCustomError) as exc_info:
        await validate_author_info(mock_issue, PublishType.DRIVER)

    assert exc_info.value.type == "not_support"


async def test_validate_author_info_bot_missing_info(
    app: App, mocker: MockerFixture, tmp_path: Path
):
    """测试验证机器人作者信息 - 缺少必要信息"""
    from src.plugins.github.plugins.remove.validation import validate_author_info
    from src.providers.validation.models import PublishType

    # 创建一个缺少 homepage 的 issue body
    mock_issue = MockIssue(
        body="### 机器人名称\n\nTestBot\n\n### 机器人项目仓库/主页链接\n\n",
        user=MockUser(login="test", id=1),
    ).as_mock(mocker)

    with pytest.raises(PydanticCustomError) as exc_info:
        await validate_author_info(mock_issue, PublishType.BOT)

    assert exc_info.value.type == "info_not_found"


async def test_validate_author_info_use_module_name_fallback(
    app: App, mocker: MockerFixture, tmp_path: Path
):
    """测试验证作者信息 - 使用 module_name 作为 name 的回退"""
    from src.plugins.github import plugin_config
    from src.plugins.github.plugins.remove.validation import validate_author_info
    from src.providers.utils import dump_json5
    from src.providers.validation.models import PublishType

    plugins = [
        {
            # 没有 name 字段
            "module_name": "nonebot_plugin_test",
            "project_link": "nonebot-plugin-test",
            "author_id": 1,
        }
    ]
    plugin_path = tmp_path / "plugins.json5"
    dump_json5(plugin_path, plugins)
    mocker.patch.object(plugin_config.input_config, "plugin_path", plugin_path)

    mock_issue = MockIssue(
        body=generate_issue_body_remove(
            "Plugin", "nonebot-plugin-test:nonebot_plugin_test"
        ),
        user=MockUser(login="test", id=1),
    ).as_mock(mocker)

    result = await validate_author_info(mock_issue, PublishType.PLUGIN)

    assert result.publish_type == PublishType.PLUGIN
    # 应该使用 module_name 作为 name
    assert result.name == "nonebot_plugin_test"
