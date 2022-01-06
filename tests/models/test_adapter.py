# type: ignore
import json
from collections import OrderedDict

import pytest
from github.Issue import Issue
from pydantic import ValidationError
from pytest_mock import MockerFixture

from src.models import AdapterPublishInfo, MyValidationError


def generate_issue_body(
    name: str = "name",
    desc: str = "desc",
    module_name: str = "module_name",
    project_link: str = "project_link",
    homepage: str = "https://v2.nonebot.dev",
    tags: list = [{"label": "test", "color": "#ffffff"}],
):
    return f"""**协议名称：**\n\n{name}\n\n**协议功能：**\n\n{desc}\n\n**PyPI 项目名：**\n\n{project_link}\n\n**协议 import 包名：**\n\n{module_name}\n\n**协议项目仓库/主页链接：**\n\n{homepage}\n\n**标签：**\n\n{json.dumps(tags)}"""


def mocked_requests_get(url: str):
    class MockResponse:
        def __init__(self, status_code: int):
            self.status_code = status_code

    if url == "https://pypi.org/pypi/project_link/json":
        return MockResponse(200)
    if url == "https://v2.nonebot.dev":
        return MockResponse(200)

    return MockResponse(404)


def test_adapter_from_issue(mocker: MockerFixture) -> None:
    """测试从 issue 中构造 AdapterPublishInfo 的情况"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)
    mock_issue: Issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body()
    mock_issue.user.login = "author"

    info = AdapterPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict()) == OrderedDict(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://v2.nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )


def test_adapter_from_issue_trailing_whitespace(mocker: MockerFixture) -> None:
    """测试末尾如果有空格的情况"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)
    mock_issue: Issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body(
        name="name ",
        desc="desc ",
        module_name="module_name ",
        project_link="project_link ",
        homepage="https://v2.nonebot.dev ",
    )
    mock_issue.user.login = "author"

    info = AdapterPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict()) == OrderedDict(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://v2.nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )


def test_adapter_info_validation_success(mocker: MockerFixture) -> None:
    """测试验证成功的情况"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)

    info = AdapterPublishInfo(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://v2.nonebot.dev",
        tags=json.dumps([{"label": "test", "color": "#ffffff"}]),
        is_official=False,
    )

    assert (
        info.validation_message
        == """> Adapter: name\n\n**✅ 所有测试通过，一切准备就绪!**\n\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff</li><li>✅ 项目 <a href="https://v2.nonebot.dev">主页</a> 返回状态码 200.</li><li>✅ 包 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI</li></code></pre></details>"""
    )

    calls = [
        mocker.call("https://pypi.org/pypi/project_link/json"),
        mocker.call("https://v2.nonebot.dev"),
    ]
    mock_requests.assert_has_calls(calls)


def test_adapter_info_validation_failed(mocker: MockerFixture) -> None:
    """测试验证失败的情况"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)
    mock_issue: Issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body(
        project_link="project_link_failed",
        homepage="https://www.baidu.com",
        tags=[{"label": "test", "color": "#fffffff"}],
    )
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        AdapterPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Adapter: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题:**\n<pre><code><li>⚠️ 包 <a href="https://pypi.org/project/project_link_failed/">project_link_failed</a> 未发布至 PyPI。<dt>请将您的包发布至 PyPI。</dt></li><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保您的项目主页可访问。</dt></li><li>第 1 个标签颜色不符合十六进制颜色码规则</li></code></pre>"""
    )

    calls = [
        mocker.call("https://pypi.org/pypi/project_link_failed/json"),
        mocker.call("https://www.baidu.com"),
    ]
    mock_requests.assert_has_calls(calls)


def test_adapter_info_validation_partial_failed(mocker: MockerFixture) -> None:
    """测试验证一部分失败的情况"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)
    mock_issue: Issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body(
        homepage="https://www.baidu.com",
    )
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        AdapterPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Adapter: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题:**\n<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保您的项目主页可访问。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff</li><li>✅ 包 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI</li></code></pre></details>"""
    )

    calls = [
        mocker.call("https://pypi.org/pypi/project_link/json"),
        mocker.call("https://www.baidu.com"),
    ]
    mock_requests.assert_has_calls(calls)
