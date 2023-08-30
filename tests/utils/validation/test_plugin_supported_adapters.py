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


async def test_plugin_supported_adapters_set(mocked_api: MockRouter) -> None:
    """不是集合的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(supported_adapters="test")

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "supported_adapters" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["type"] == "type_error.set"
    assert result["errors"][0]["msg"] == "值不是合法的集合"

    assert mocked_api["homepage"].called


async def test_plugin_supported_adapters_json(mocked_api: MockRouter) -> None:
    """不是 JSON 的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(supported_adapters="test", skip_test=True)

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "supported_adapters" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["type"] == "value_error.json"
    assert result["errors"][0]["msg"] == "JSON 格式不合法"

    assert mocked_api["homepage"].called
