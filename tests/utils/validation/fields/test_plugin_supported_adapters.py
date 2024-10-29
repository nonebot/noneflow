from inline_snapshot import snapshot
from respx import MockRouter

from tests.utils.validation.utils import generate_plugin_data


async def test_plugin_supported_adapters_none(mocked_api: MockRouter) -> None:
    """支持所有适配器"""

    from src.providers.validation import PublishType, validate_info
    from src.providers.validation.models import PluginPublishInfo

    data = generate_plugin_data()

    result = validate_info(PublishType.PLUGIN, data, [])

    assert result.valid
    assert result.type == PublishType.PLUGIN
    assert isinstance(result.info, PluginPublishInfo)
    assert result.raw_data == snapshot(
        {
            "author": "author",
            "module_name": "module_name",
            "project_link": "project_link",
            "tags": '[{"label": "test", "color": "#ffffff"}]',
            "name": "name",
            "desc": "desc",
            "homepage": "https://nonebot.dev",
            "type": "application",
            "supported_adapters": None,
            "skip_test": False,
            "metadata": True,
            "author_id": 1,
            "load": True,
            "version": "0.0.1",
            "test_output": "test_output",
            "time": "2023-09-01T00:00:00+00:00Z",
        }
    )
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00+00:00Z",
            "name": "name",
            "desc": "desc",
            "author": "author",
            "author_id": 1,
            "homepage": "https://nonebot.dev",
            "tags": [{"label": "test", "color": "#ffffff"}],
            "type": "application",
            "supported_adapters": None,
            "load": True,
            "metadata": True,
            "skip_test": False,
            "version": "0.0.1",
            "test_output": "test_output",
        }
    )

    assert mocked_api["homepage"].called


async def test_plugin_supported_adapters_set(mocked_api: MockRouter) -> None:
    """不是集合的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_plugin_data(supported_adapters="test")

    result = validate_info(PublishType.PLUGIN, data, [])

    assert not result.valid
    assert result.type == PublishType.PLUGIN
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00+00:00Z",
            "name": "name",
            "desc": "desc",
            "author": "author",
            "author_id": 1,
            "homepage": "https://nonebot.dev",
            "tags": [{"label": "test", "color": "#ffffff"}],
            "type": "application",
            "load": True,
            "metadata": True,
            "skip_test": False,
            "version": "0.0.1",
            "test_output": "test_output",
        }
    )
    assert result.info is None
    assert result.errors == snapshot(
        [
            {
                "type": "set_type",
                "loc": ("supported_adapters",),
                "msg": "值不是合法的集合",
                "input": "test",
            }
        ]
    )

    assert mocked_api["homepage"].called


async def test_plugin_supported_adapters_json(mocked_api: MockRouter) -> None:
    """不是 JSON 跳过测试的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_plugin_data(supported_adapters="test", skip_test=True)

    result = validate_info(PublishType.PLUGIN, data, [])

    assert not result.valid
    assert result.type == PublishType.PLUGIN
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00+00:00Z",
            "name": "name",
            "desc": "desc",
            "author": "author",
            "author_id": 1,
            "homepage": "https://nonebot.dev",
            "tags": [{"label": "test", "color": "#ffffff"}],
            "type": "application",
            "load": True,
            "metadata": True,
            "skip_test": True,
            "version": "0.0.1",
            "test_output": "test_output",
        }
    )
    assert result.info is None
    assert result.errors == snapshot(
        [
            {
                "type": "json_type",
                "loc": ("supported_adapters",),
                "msg": "JSON 格式不合法",
                "input": "test",
            }
        ]
    )

    assert mocked_api["homepage"].called


async def test_plugin_supported_adapters_missing_adapters(
    mocked_api: MockRouter,
) -> None:
    """缺少适配器的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_plugin_data(
        supported_adapters={"nonebot.adapters.qq"}, skip_test=True
    )

    result = validate_info(PublishType.PLUGIN, data, [])

    assert not result.valid
    assert result.type == PublishType.PLUGIN
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00+00:00Z",
            "name": "name",
            "desc": "desc",
            "author": "author",
            "author_id": 1,
            "homepage": "https://nonebot.dev",
            "tags": [{"label": "test", "color": "#ffffff"}],
            "type": "application",
            "load": True,
            "metadata": True,
            "skip_test": True,
            "version": "0.0.1",
            "test_output": "test_output",
        }
    )
    assert result.info is None
    assert result.errors == snapshot(
        [
            {
                "type": "supported_adapters.missing",
                "loc": ("supported_adapters",),
                "msg": "适配器 nonebot.adapters.qq 不存在",
                "input": {"nonebot.adapters.qq"},
                "ctx": {
                    "missing_adapters": ["nonebot.adapters.qq"],
                    "missing_adapters_str": "nonebot.adapters.qq",
                },
            }
        ]
    )

    assert mocked_api["homepage"].called
