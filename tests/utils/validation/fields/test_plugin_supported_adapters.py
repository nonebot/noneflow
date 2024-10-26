from inline_snapshot import snapshot
from respx import MockRouter

from tests.utils.validation.utils import generate_plugin_data


async def test_plugin_supported_adapters_none(mocked_api: MockRouter) -> None:
    """支持所有适配器"""
    from src.providers.validation import PublishType, validate_info

    data, context = generate_plugin_data()

    result = validate_info(PublishType.PLUGIN, data, context)

    assert result.valid
    assert "supported_adapters" in result.valid_data
    assert not result.errors

    assert mocked_api["homepage"].called


async def test_plugin_supported_adapters_set(mocked_api: MockRouter) -> None:
    """不是集合的情况"""
    from src.providers.validation import PublishType, validate_info

    data, context = generate_plugin_data(supported_adapters="test")

    result = validate_info(PublishType.PLUGIN, data, context)

    assert not result.valid
    assert "supported_adapters" not in result.valid_data
    assert result.errors == [
        snapshot(
            {
                "type": "set_type",
                "loc": ("supported_adapters",),
                "msg": "值不是合法的集合",
                "input": "test",
            }
        )
    ]

    assert mocked_api["homepage"].called


async def test_plugin_supported_adapters_json(mocked_api: MockRouter) -> None:
    """不是 JSON 跳过测试的情况"""
    from src.providers.validation import PublishType, validate_info

    data, context = generate_plugin_data(supported_adapters="test", skip_test=True)

    result = validate_info(PublishType.PLUGIN, data, context)

    assert not result.valid
    assert "supported_adapters" not in result.valid_data
    assert result.errors == [
        snapshot(
            {
                "type": "json_type",
                "loc": ("supported_adapters",),
                "msg": "JSON 格式不合法",
                "input": "test",
            }
        )
    ]

    assert mocked_api["homepage"].called


async def test_plugin_supported_adapters_missing_adapters(
    mocked_api: MockRouter,
) -> None:
    """缺少适配器的情况"""
    from src.providers.validation import PublishType, validate_info

    data, context = generate_plugin_data(
        supported_adapters={"nonebot.adapters.qq"}, skip_test=True
    )

    result = validate_info(PublishType.PLUGIN, data, context)

    assert not result.valid
    assert "supported_adapters" not in result.valid_data
    assert result.errors == [
        snapshot(
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
        )
    ]

    assert mocked_api["homepage"].called
