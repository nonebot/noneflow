import json

from respx import MockRouter

from tests.utils.validation.utils import generate_plugin_data


async def test_tags_color_missing(mocked_api: MockRouter) -> None:
    """测试标签缺少颜色的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(tags=[{"label": "test"}])

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "tags" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("tags", 0, "color")
    assert result["errors"][0]["type"] == "missing"
    assert result["errors"][0]["msg"] == "字段不存在"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_tags_color_invalid(mocked_api: MockRouter) -> None:
    """测试标签颜色不正确的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(tags=[{"label": "test", "color": "#adbcdef"}])

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "tags" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("tags", 0, "color")
    assert result["errors"][0]["type"] == "color_error"
    assert result["errors"][0]["msg"] == "颜色格式不正确"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_tags_label_invalid(mocked_api: MockRouter) -> None:
    """测试标签名称不正确的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(tags=[{"label": "12345678901", "color": "#adbcde"}])

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "tags" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("tags", 0, "label")
    assert result["errors"][0]["type"] == "string_too_long"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_tags_number_invalid(mocked_api: MockRouter) -> None:
    """测试标签数量不正确的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(
        tags=[
            {"label": "1", "color": "#ffffff"},
            {"label": "2", "color": "#ffffff"},
            {"label": "3", "color": "#ffffff"},
            {"label": "4", "color": "#ffffff"},
        ]
    )

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "tags" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("tags",)
    assert result["errors"][0]["type"] == "too_long"
    assert result["errors"][0]["msg"] == "列表长度不能超过 3 个元素"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_tags_json_invalid(mocked_api: MockRouter) -> None:
    """测试标签 json 格式不正确的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data()
    data["tags"] = json.dumps([{"label": "1", "color": "#ffffff"}]) + "1"

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "tags" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("tags",)
    assert result["errors"][0]["type"] == "json_type"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_tags_json_not_list(mocked_api: MockRouter) -> None:
    """测试标签 json 不是列表的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data()
    data["tags"] = json.dumps({"test": "test"})

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "tags" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("tags",)
    assert result["errors"][0]["type"] == "list_type"
    assert result["errors"][0]["msg"] == "值不是合法的列表"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_tags_json_not_dict(mocked_api: MockRouter) -> None:
    """测试标签 json 是列表但列表里不全是字典的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(tags=[{"label": "1", "color": "#ffffff"}, "1"])

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "tags" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("tags", 1)
    assert result["errors"][0]["type"] == "model_type"
    assert result["errors"][0]["msg"] == "值不是合法的字典"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called
