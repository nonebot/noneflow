import json

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture
from respx import MockRouter


async def test_adapter_tags_color_missing(mocked_api: MockRouter) -> None:
    """测试标签缺少颜色的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

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
    from src.plugins.publish.validation import AdapterPublishInfo

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
    assert "标签颜色错误<dt>请确保标签颜色符合十六进制颜色码规则。</dt>" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_label_invalid(mocked_api: MockRouter) -> None:
    """测试标签名称不正确的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

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
    assert "标签名称过长<dt>请确保标签名称不超过 10 个字符。</dt>" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_number_invalid(mocked_api: MockRouter) -> None:
    """测试标签数量不正确的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

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
    assert "⚠️ 标签数量过多。<dt>请确保标签数量不超过 3 个。</dt>" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_json_invalid(mocked_api: MockRouter) -> None:
    """测试标签 json 格式不正确的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

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
    assert "⚠️ 标签解码失败。<dt>请确保标签为 JSON 格式。</dt>" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_json_not_list(mocked_api: MockRouter) -> None:
    """测试标签 json 不是列表的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

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
    assert "⚠️ 标签格式错误。<dt>请确保标签为列表。</dt>" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_tags_json_not_dict(mocked_api: MockRouter) -> None:
    """测试标签 json 是列表但列表里不全是字典的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

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
    assert "⚠️ 标签格式错误。<dt>请确保标签列表内均为字典。</dt>" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called
