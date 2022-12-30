import json

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture


def generate_issue_body(
    name: str = "name",
    desc: str = "desc",
    module_name: str = "module_name",
    project_link: str = "project_link",
    homepage: str = "https://v2.nonebot.dev",
    tags: list = [{"label": "test", "color": "#ffffff"}],
):
    return f"""**协议名称：**\n\n{name}\n\n**协议功能：**\n\n{desc}\n\n**PyPI 项目名：**\n\n{project_link}\n\n**协议 import 包名：**\n\n{module_name}\n\n**协议项目仓库/主页链接：**\n\n{homepage}\n\n**标签：**\n\n{json.dumps(tags)}"""


def mocked_httpx_get(url: str):
    class MockResponse:
        def __init__(self, status_code: int):
            self.status_code = status_code

    if url == "https://pypi.org/pypi/project_link/json":
        return MockResponse(200)
    if url == "https://v2.nonebot.dev":
        return MockResponse(200)

    return MockResponse(404)


def test_adapter_tags_color_missing(mocker: MockerFixture) -> None:
    """测试标签缺少颜色的情况"""
    from src.models import AdapterPublishInfo

    mock_httpx = mocker.patch("httpx.get", side_effect=mocked_httpx_get)

    with pytest.raises(ValidationError) as e:
        info = AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://v2.nonebot.dev",
            tags=json.dumps([{"label": "test"}]),  # type: ignore
            is_official=False,
        )
    assert "color\n  field required (type=value_error.missing)" in str(e.value)


def test_adapter_tags_color_invalid(mocker: MockerFixture) -> None:
    """测试标签颜色不正确的情况"""
    from src.models import AdapterPublishInfo

    mock_httpx = mocker.patch("httpx.get", side_effect=mocked_httpx_get)

    with pytest.raises(ValidationError) as e:
        info = AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://v2.nonebot.dev",
            tags=json.dumps([{"label": "test", "color": "#adbcdef"}]),  # type: ignore
            is_official=False,
        )
    assert "标签颜色错误<dt>请确保标签颜色符合十六进制颜色码规则。</dt>" in str(e.value)


def test_adapter_tags_label_invalid(mocker: MockerFixture) -> None:
    """测试标签名称不正确的情况"""
    from src.models import AdapterPublishInfo

    mock_httpx = mocker.patch("httpx.get", side_effect=mocked_httpx_get)

    with pytest.raises(ValidationError) as e:
        info = AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://v2.nonebot.dev",
            tags=json.dumps([{"label": "12345678901", "color": "#adbcde"}]),  # type: ignore
            is_official=False,
        )
    assert "标签名称过长<dt>请确保标签名称不超过 10 个字符。</dt>" in str(e.value)


def test_adapter_tags_number_invalid(mocker: MockerFixture) -> None:
    """测试标签数量不正确的情况"""
    from src.models import AdapterPublishInfo

    mock_httpx = mocker.patch("httpx.get", side_effect=mocked_httpx_get)

    with pytest.raises(ValidationError) as e:
        info = AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://v2.nonebot.dev",
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


def test_adapter_tags_json_invalid(mocker: MockerFixture) -> None:
    """测试标签 json 格式不正确的情况"""
    from src.models import AdapterPublishInfo

    mock_httpx = mocker.patch("httpx.get", side_effect=mocked_httpx_get)

    with pytest.raises(ValidationError) as e:
        info = AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://v2.nonebot.dev",
            tags=json.dumps([{"label": "1", "color": "#ffffff"}]) + "1",  # type: ignore
            is_official=False,
        )
    assert "⚠️ 标签解码失败。<dt>请确保标签格式正确。</dt>" in str(e.value)


def test_adapter_tags_json_not_list(mocker: MockerFixture) -> None:
    """测试标签 json 不是列表的情况"""
    from src.models import AdapterPublishInfo

    mock_httpx = mocker.patch("httpx.get", side_effect=mocked_httpx_get)

    with pytest.raises(ValidationError) as e:
        info = AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://v2.nonebot.dev",
            tags="1",  # type: ignore
            is_official=False,
        )
    assert "⚠️ 标签格式错误。<dt>请确保标签为列表。</dt>" in str(e.value)


def test_adapter_tags_json_not_dict(mocker: MockerFixture) -> None:
    """测试标签 json 是列表但列表里不全是字典的情况"""
    from src.models import AdapterPublishInfo

    mock_httpx = mocker.patch("httpx.get", side_effect=mocked_httpx_get)

    with pytest.raises(ValidationError) as e:
        info = AdapterPublishInfo(
            module_name="module_name",
            project_link="project_link",
            name="name",
            desc="desc",
            author="author",
            homepage="https://v2.nonebot.dev",
            tags=json.dumps([{"label": "1", "color": "#ffffff"}, "1"]),  # type: ignore
            is_official=False,
        )
    assert "⚠️ 标签格式错误。<dt>请确保标签列表内均为字典。</dt>" in str(e.value)
