import json

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture
from respx import MockRouter


async def test_pypi_project_name_invalid(mocked_api: MockRouter) -> None:
    """测试 PyPI 项目名错误的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link/",
            name="name",
            desc="desc",
            author="author",
            homepage="https://nonebot.dev",
            tags=json.dumps([]),  # type: ignore
            is_official=False,
        )
    assert "⚠️ PyPI 项目名 project_link/ 不符合规范。<dt>请确保项目名正确。</dt>" in str(e.value)

    assert mocked_api["homepage"].called


async def test_module_name_invalid(mocked_api: MockRouter) -> None:
    """测试模块名称不正确的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="1module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://nonebot.dev",
            tags=json.dumps([]),  # type: ignore
            is_official=False,
        )
    assert "⚠️ 包名 1module_name 不符合规范。<dt>请确保包名正确。</dt>" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_name_duplication(mocked_api: MockRouter) -> None:
    """测试名称重复的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="module_name1",
            project_link="project_link1",
            name="name",
            desc="desc",
            author="author",
            homepage="https://nonebot.dev",
            tags=json.dumps([]),  # type: ignore
            is_official=False,
        )
    assert (
        "⚠️ PyPI 项目名 project_link1 加包名 module_name1 的值与商店重复。<dt>请确保没有重复发布。</dt>"
        in str(e.value)
    )

    assert mocked_api["project_link1"].called
    assert mocked_api["homepage"].called


async def test_name_too_long(mocked_api: MockRouter) -> None:
    """测试名称过长的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="looooooooooooooooooooooooooooooooooooooooooooooooooooooooong",
            desc="desc",
            author="author",
            homepage="https://nonebot.dev",
            tags=json.dumps([]),  # type: ignore
            is_official=False,
        )
    assert "⚠️ 名称过长。<dt>请确保名称不超过 50 个字符。</dt>" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called
