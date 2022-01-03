# type: ignore
import json
from collections import OrderedDict

from github.Issue import Issue
from pytest_mock import MockerFixture

from src.models import PluginPublishInfo


def generate_issue_body(
    name: str = "name",
    desc: str = "desc",
    module_name: str = "module_name",
    project_link: str = "project_link",
    homepage: str = "https://v2.nonebot.dev",
    tags: list = [{"label": "test", "color": "#ffffff"}],
):
    return f"""**插件名称：**\n\n{name}\n\n**插件功能：**\n\n{desc}\n\n**PyPI 项目名：**\n\n{project_link}\n\n**插件 import 包名：**\n\n{module_name}\n\n**插件项目仓库/主页链接：**\n\n{homepage}\n\n**标签：**\n\n{json.dumps(tags)}"""


def test_plugin_info() -> None:
    info = PluginPublishInfo(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )

    assert OrderedDict(info.dict()) == OrderedDict(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )


def test_plugin_from_issue(mocker: MockerFixture) -> None:
    mock_issue: Issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body(homepage="https://www.baidu.com")
    mock_issue.user.login = "author"

    info = PluginPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict()) == OrderedDict(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )


def test_plugin_from_issue_trailing_whitespace(mocker: MockerFixture) -> None:
    """测试末尾如果有空格的情况"""
    mock_issue: Issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body(
        module_name="module_name ",
        project_link="project_link ",
        name="name ",
        desc="desc ",
        homepage="https://www.baidu.com ",
    )
    mock_issue.user.login = "author"

    info = PluginPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict()) == OrderedDict(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )


def mocked_requests_get(url: str):
    class MockResponse:
        def __init__(self, status_code: int):
            self.status_code = status_code

    if url == "https://pypi.org/pypi/project_link/json":
        return MockResponse(200)
    if url == "https://v2.nonebot.dev":
        return MockResponse(200)

    return MockResponse(404)


def test_plugin_info_validation_success(mocker: MockerFixture) -> None:
    """测试验证成功的情况"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)

    info = PluginPublishInfo(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://v2.nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )

    assert info.is_valid
    assert (
        info.validation_message
        == """> Plugin: name\n\n**✅ All tests passed, you are ready to go!**\n\n<details><summary>Report Detail</summary><pre><code><li>✅ Project <a href="https://v2.nonebot.dev">homepage</a> returns 200.</li><li>✅ Package <a href="https://pypi.org/project/project_link/">project_link</a> is available on PyPI.</li></code></pre></details>"""
    )

    calls = [
        mocker.call("https://pypi.org/pypi/project_link/json"),
        mocker.call("https://v2.nonebot.dev"),
    ]
    mock_requests.assert_has_calls(calls)


def test_plugin_info_validation_failed(mocker: MockerFixture) -> None:
    """测试验证失败的情况"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)

    info = PluginPublishInfo(
        module_name="module_name",
        project_link="project_link_failed",
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )

    assert not info.is_valid
    assert (
        info.validation_message
        == """> Plugin: name\n\n**⚠️ We have found following problem(s) in pre-publish progress:**\n<pre><code><li>⚠️ Project <a href="https://www.baidu.com">homepage</a> returns 404.<dt>Please make sure that your project has a publicly visible homepage.</dt></li><li>⚠️ Package <a href="https://pypi.org/project/project_link_failed/">project_link_failed</a> is not available on PyPI.<dt>Please publish your package to PyPI.</dt></li></code></pre>"""
    )

    calls = [
        mocker.call("https://pypi.org/pypi/project_link_failed/json"),
        mocker.call("https://www.baidu.com"),
    ]
    mock_requests.assert_has_calls(calls)


def test_plugin_info_validation_partial_failed(mocker: MockerFixture) -> None:
    """测试验证一部分失败的情况"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)

    info = PluginPublishInfo(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )

    assert not info.is_valid
    assert (
        info.validation_message
        == """> Plugin: name\n\n**⚠️ We have found following problem(s) in pre-publish progress:**\n<pre><code><li>⚠️ Project <a href="https://www.baidu.com">homepage</a> returns 404.<dt>Please make sure that your project has a publicly visible homepage.</dt></li></code></pre>\n<details><summary>Report Detail</summary><pre><code><li>✅ Package <a href="https://pypi.org/project/project_link/">project_link</a> is available on PyPI.</li></code></pre></details>"""
    )

    calls = [
        mocker.call("https://pypi.org/pypi/project_link/json"),
        mocker.call("https://www.baidu.com"),
    ]
    mock_requests.assert_has_calls(calls)
