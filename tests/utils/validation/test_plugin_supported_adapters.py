from respx import MockRouter

from tests.utils.validation.utils import generate_plugin_data


async def test_plugin_supported_adapters_none(mocked_api: MockRouter) -> None:
    """支持所有适配器"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data()

    result = validate_info(PublishType.PLUGIN, data)

    assert result["valid"]
    assert "supported_adapters" in result["data"]
    assert not result["errors"]

    assert mocked_api["homepage"].called


async def test_plugin_supported_adapters_iterable(mocked_api: MockRouter) -> None:
    """不是列表的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(supported_adapters="test")  # type: ignore

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "supported_adapters" not in result["data"]
    assert result["errors"]

    assert mocked_api["homepage"].called
