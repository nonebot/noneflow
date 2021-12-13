from collections import OrderedDict

import requests
from github.Issue import Issue
from pytest_mock import MockerFixture

from src.models import AdapterPublishInfo


def test_adapter_info() -> None:
    info = AdapterPublishInfo(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
    )

    assert OrderedDict(info.dict()) == OrderedDict(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
    )


def test_adapter_from_issue(mocker: MockerFixture) -> None:
    body = """
        <!-- DO NOT EDIT ! -->
        <!--
        - module_name: module_name
        - project_link: project_link
        - name: name
        - desc: desc
        - homepage: https://www.baidu.com
        - tags: tag
        - is_official: false
        -->
        """
    mock_issue: Issue = mocker.MagicMock()  # type: ignore
    mock_issue.body = body  # type: ignore
    mock_issue.user.login = "author"  # type: ignore

    info = AdapterPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict()) == OrderedDict(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
    )


def test_adapter_from_issue_trailing_whitespace(mocker: MockerFixture) -> None:
    """测试末尾如果有空格的情况"""
    body = """
        <!-- DO NOT EDIT ! -->
        <!--
        - module_name: module_name 
        - project_link: project_link 
        - name: my name  
        - desc: desc 
        - homepage: https://www.baidu.com 
        - tags: tag, tag 2 
        - is_official: false 
        -->
    """
    mock_issue: Issue = mocker.MagicMock()  # type: ignore
    mock_issue.body = body  # type: ignore
    mock_issue.user.login = "author"  # type: ignore

    info = AdapterPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict()) == OrderedDict(
        module_name="module_name",
        project_link="project_link",
        name="my name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag", "tag 2"],
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


def test_adapter_info_validation_success(mocker: MockerFixture) -> None:
    """测试验证成功的情况"""
    mocker.patch("requests.get", side_effect=mocked_requests_get)

    info = AdapterPublishInfo(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://v2.nonebot.dev",
        tags=["tag"],
        is_official=False,
    )

    assert info.is_valid
    assert (
        info.validation_message
        == """> Adapter: name\n\n**✅ All tests passed, you are ready to go!**\n\n<details><summary>Report Detail</summary><pre><code><li>✅ Project <a href="https://v2.nonebot.dev">homepage</a> returns 200.</li><li>✅ Package <a href="https://pypi.org/project/project_link/">project_link</a> is available on PyPI.</li></code></pre></details>"""
    )

    calls = [  # type: ignore
        mocker.call("https://pypi.org/pypi/project_link/json"),  # type: ignore
        mocker.call("https://v2.nonebot.dev"),  # type: ignore
    ]
    requests.get.assert_has_calls(calls)  # type: ignore


def test_adapter_info_validation_failed(mocker: MockerFixture) -> None:
    """测试验证失败的情况"""
    mocker.patch("requests.get", side_effect=mocked_requests_get)

    info = AdapterPublishInfo(
        module_name="module_name",
        project_link="project_link_failed",
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
    )

    assert not info.is_valid
    assert (
        info.validation_message
        == """> Adapter: name\n\n**⚠️ We have found following problem(s) in pre-publish progress:**\n<pre><code><li>⚠️ Project <a href="https://www.baidu.com">homepage</a> returns 404.<dt>Please make sure that your project has a publicly visible homepage.</dt></li><li>⚠️ Package <a href="https://pypi.org/project/project_link_failed/">project_link_failed</a> is not available on PyPI.<dt>Please publish your package to PyPI.</dt></li></code></pre>"""
    )

    calls = [  # type: ignore
        mocker.call("https://pypi.org/pypi/project_link_failed/json"),  # type: ignore
        mocker.call("https://www.baidu.com"),  # type: ignore
    ]
    requests.get.assert_has_calls(calls)  # type: ignore


def test_adapter_info_validation_partial_failed(mocker: MockerFixture) -> None:
    """测试验证一部分失败的情况"""
    mocker.patch("requests.get", side_effect=mocked_requests_get)

    info = AdapterPublishInfo(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
    )

    assert not info.is_valid
    assert (
        info.validation_message
        == """> Adapter: name\n\n**⚠️ We have found following problem(s) in pre-publish progress:**\n<pre><code><li>⚠️ Project <a href="https://www.baidu.com">homepage</a> returns 404.<dt>Please make sure that your project has a publicly visible homepage.</dt></li></code></pre>\n<details><summary>Report Detail</summary><pre><code><li>✅ Package <a href="https://pypi.org/project/project_link/">project_link</a> is available on PyPI.</li></code></pre></details>"""
    )

    calls = [  # type: ignore
        mocker.call("https://pypi.org/pypi/project_link/json"),  # type: ignore
        mocker.call("https://www.baidu.com"),  # type: ignore
    ]
    requests.get.assert_has_calls(calls)  # type: ignore
