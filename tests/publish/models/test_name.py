import json

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture


def mocked_httpx_get(url: str):
    class MockResponse:
        def __init__(self, status_code: int):
            self.status_code = status_code

    if url == "https://pypi.org/pypi/project_link/json":
        return MockResponse(200)
    if url == "https://pypi.org/pypi/project_link1/json":
        return MockResponse(200)
    if url == "https://v2.nonebot.dev":
        return MockResponse(200)

    return MockResponse(404)


async def test_pypi_project_name_invalid(mocker: MockerFixture) -> None:
    """测试 PyPI 项目名错误的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

    mock_httpx = mocker.patch("httpx.get", side_effect=mocked_httpx_get)

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link/",
            name="name",
            desc="desc",
            author="author",
            homepage="https://v2.nonebot.dev",
            tags=json.dumps([]),  # type: ignore
            is_official=False,
        )
    assert "⚠️ PyPI 项目名 project_link/ 不符合规范。<dt>请确保项目名正确。</dt>" in str(e.value)

    mock_httpx.assert_called_once_with("https://v2.nonebot.dev")


async def test_module_name_invalid(mocker: MockerFixture) -> None:
    """测试模块名称不正确的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

    mock_httpx = mocker.patch("httpx.get", side_effect=mocked_httpx_get)

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="1module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://v2.nonebot.dev",
            tags=json.dumps([]),  # type: ignore
            is_official=False,
        )
    assert "⚠️ 包名 1module_name 不符合规范。<dt>请确保包名正确。</dt>" in str(e.value)

    mock_httpx.assert_has_calls(
        [
            mocker.call("https://pypi.org/pypi/project_link/json"),
            mocker.call("https://v2.nonebot.dev"),
        ]  # type: ignore
    )


async def test_name_duplication(mocker: MockerFixture) -> None:
    """测试名称重复的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

    mock_httpx = mocker.patch("httpx.get", side_effect=mocked_httpx_get)

    with pytest.raises(ValidationError) as e:
        AdapterPublishInfo(
            module_name="module_name1",
            project_link="project_link1",
            name="name",
            desc="desc",
            author="author",
            homepage="https://v2.nonebot.dev",
            tags=json.dumps([]),  # type: ignore
            is_official=False,
        )
    assert (
        "⚠️ PyPI 项目名 project_link1 加包名 module_name1 的值与商店重复。<dt>请确保没有重复发布。</dt>"
        in str(e.value)
    )

    mock_httpx.assert_has_calls(
        [
            mocker.call("https://pypi.org/pypi/project_link1/json"),
            mocker.call("https://v2.nonebot.dev"),
        ]  # type: ignore
    )
