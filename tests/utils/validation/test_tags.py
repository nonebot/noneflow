import json

import pytest
from pydantic import ValidationError
from respx import MockRouter


async def test_adapter_tags_color_missing(mocked_api: MockRouter) -> None:
    """测试标签缺少颜色的情况"""
    from src.utils.validation import AdapterPublishInfo

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://nonebot.dev",
            tags=json.dumps([{"label": "test"}]),  # type: ignore
            is_official=False,
        )
    assert "color\n  field required (type=value_error.missing)" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_color_invalid(mocked_api: MockRouter) -> None:
    """测试标签颜色不正确的情况"""
    from src.utils.validation import AdapterPublishInfo

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://nonebot.dev",
            tags=json.dumps([{"label": "test", "color": "#adbcdef"}]),  # type: ignore
            is_official=False,
        )
    assert "string not recognised as a valid color" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_label_invalid(mocked_api: MockRouter) -> None:
    """测试标签名称不正确的情况"""
    from src.utils.validation import AdapterPublishInfo

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://nonebot.dev",
            tags=json.dumps([{"label": "12345678901", "color": "#adbcde"}]),  # type: ignore
            is_official=False,
        )
    assert (
        "ensure this value has at most 10 characters (type=value_error.any_str.max_length; limit_value=10)"
        in str(e.value)
    )

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_number_invalid(mocked_api: MockRouter) -> None:
    """测试标签数量不正确的情况"""
    from src.utils.validation import AdapterPublishInfo

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://nonebot.dev",
            tags=json.dumps(
                [
                    {"label": "1", "color": "#ffffff"},
                    {"label": "2", "color": "#ffffff"},
                    {"label": "3", "color": "#ffffff"},
                    {"label": "4", "color": "#ffffff"},
                ]
            ),  # type: ignore
            is_official=False,
        )
    assert (
        "ensure this value has at most 3 items (type=value_error.list.max_items; limit_value=3)"
        in str(e.value)
    )

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
    from src.utils.validation import AdapterPublishInfo

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://nonebot.dev",
            tags="1",  # type: ignore
            is_official=False,
        )
    assert "value is not a valid list (type=type_error.list)" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_json_not_dict(mocked_api: MockRouter) -> None:
    """测试标签 json 是列表但列表里不全是字典的情况"""
    from src.utils.validation import AdapterPublishInfo

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://nonebot.dev",
            tags=json.dumps([{"label": "1", "color": "#ffffff"}, "1"]),  # type: ignore
            is_official=False,
        )
    assert "value is not a valid dict (type=type_error.dict)" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called
