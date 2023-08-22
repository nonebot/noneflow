import json

import pytest
from pydantic import ValidationError
from respx import MockRouter


async def test_pypi_project_name_invalid(mocked_api: MockRouter) -> None:
    """测试 PyPI 项目名错误的情况"""
    from src.utils.validation import AdapterPublishInfo

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
    assert "PyPI 项目名不符合规范。" in str(e.value)

    assert mocked_api["homepage"].called


async def test_module_name_invalid(mocked_api: MockRouter) -> None:
    """测试模块名称不正确的情况"""
    from src.utils.validation import AdapterPublishInfo

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
            previous_data=[],
        )
    assert "包名不符合规范" in str(e.value)

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_name_duplication(mocked_api: MockRouter) -> None:
    """测试名称重复的情况"""
    from src.utils.validation import AdapterPublishInfo

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
            previous_data=[
                {
                    "module_name": "module_name1",
                    "project_link": "project_link1",
                    "name": "name",
                    "desc": "desc",
                    "author": "author",
                }
            ],
        )
    assert "PyPI 项目名 project_link1 加包名 module_name1 的值与商店重复" in str(e.value)

    assert mocked_api["project_link1"].called
    assert mocked_api["homepage"].called


async def test_name_too_long(mocked_api: MockRouter) -> None:
    """测试名称过长的情况"""
    from src.utils.validation import AdapterPublishInfo

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
    assert (
        "ensure this value has at most 50 characters (type=value_error.any_str.max_length; limit_value=50)"
        in str(e.value)
    )

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called
