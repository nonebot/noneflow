from respx import MockRouter


async def test_validate_plugin_info(mocked_api: MockRouter) -> None:
    """验证插件信息"""
    from src.utils.store_test.validation import StorePlugin, validate_plugin_info

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author="author",
        tags=[],
        is_official=False,
    )

    result = await validate_plugin_info(False, plugin, None)

    assert not result["result"]
    assert result["output"]
    assert "name" not in result["output"]["data"]
    assert result["output"]["errors"]
    assert result["output"]["errors"][0]["loc"] == ("metadata",)
    assert result["output"]["errors"][0]["type"] == "value_error.metadata"

    assert not mocked_api["homepage"].called
