import json

import pytest
from pydantic import ValidationError
from respx import MockRouter

from tests.utils.validation.utils import generate_plugin_data


async def test_adapter_tags_color_missing(mocked_api: MockRouter) -> None:
    """测试标签缺少颜色的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(tags=[{"label": "test"}])

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "tags" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("tags", 0, "color")
    assert result["errors"][0]["type"] == "value_error.missing"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_color_invalid(mocked_api: MockRouter) -> None:
    """测试标签颜色不正确的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(tags=[{"label": "test", "color": "#adbcdef"}])

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "tags" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("tags", 0, "color")
    assert result["errors"][0]["type"] == "value_error.color"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_label_invalid(mocked_api: MockRouter) -> None:
    """测试标签名称不正确的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(tags=[{"label": "12345678901", "color": "#adbcde"}])

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "tags" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("tags", 0, "label")
    assert result["errors"][0]["type"] == "value_error.any_str.max_length"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_number_invalid(mocked_api: MockRouter) -> None:
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
    assert result["errors"][0]["type"] == "value_error.list.max_items"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_json_invalid(mocked_api: MockRouter) -> None:
    """测试标签 json 格式不正确的情况"""
    from src.utils.validation import AdapterPublishInfo

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://nonebot.dev",
            tags=json.dumps([{"label": "1", "color": "#ffffff"}]) + "1",  # type: ignore
            is_official=False,
        )
    assert "Invalid JSON (type=value_error.json)" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_json_not_list(mocked_api: MockRouter) -> None:
    """测试标签 json 不是列表的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data()
    data["tags"] = "test"

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "tags" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("tags",)
    assert result["errors"][0]["type"] == "value_error.json"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_json_not_dict(mocked_api: MockRouter) -> None:
    """测试标签 json 是列表但列表里不全是字典的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(tags=[{"label": "1", "color": "#ffffff"}, "1"])

    result = validate_info(PublishType.PLUGIN, data)

    assert not result["valid"]
    assert "tags" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("tags", 1)
    assert result["errors"][0]["type"] == "type_error.dict"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called
