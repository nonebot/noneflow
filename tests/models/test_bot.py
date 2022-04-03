# type: ignore
import json
from collections import OrderedDict
from typing import Union

from github.Issue import Issue
from pytest_mock import MockerFixture

from src.models import BotPublishInfo, MyValidationError


def generate_issue_body(
    name: str = "name",
    desc: str = "desc",
    homepage: str = "https://v2.nonebot.dev",
    tags: Union[list, str] = [{"label": "test", "color": "#ffffff"}],
):
    if isinstance(tags, list):
        tags = json.dumps(tags)
    return f"""**机器人名称：**\n\n{name}\n\n**机器人功能：**\n\n{desc}\n\n**机器人项目仓库/主页链接：**\n\n{homepage}\n\n**标签：**\n\n{tags}"""


def mocked_requests_get(url: str):
    class MockResponse:
        def __init__(self, status_code: int):
            self.status_code = status_code

    if url == "https://pypi.org/pypi/project_link/json":
        return MockResponse(200)
    if url == "https://v2.nonebot.dev":
        return MockResponse(200)

    return MockResponse(404)


def test_bot_from_issue(mocker: MockerFixture) -> None:
    """测试从 issue 中构造 BotPublishInfo"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)
    mock_issue: Issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body()
    mock_issue.user.login = "author"

    info = BotPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict()) == OrderedDict(
        name="name",
        desc="desc",
        author="author",
        homepage="https://v2.nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )
    mock_requests.assert_called_once_with("https://v2.nonebot.dev")


def test_bot_from_issue_trailing_whitespace(mocker: MockerFixture) -> None:
    """测试末尾如果有空格的情况"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)
    mock_issue: Issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body(
        name="name ",
        desc="desc ",
        homepage="https://v2.nonebot.dev ",
    )
    mock_issue.user.login = "author"

    info = BotPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict()) == OrderedDict(
        name="name",
        desc="desc",
        author="author",
        homepage="https://v2.nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )
    mock_requests.assert_called_once_with("https://v2.nonebot.dev")


def test_bot_info_validation_success(mocker: MockerFixture) -> None:
    """测试验证成功的情况"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)

    info = BotPublishInfo(
        name="name",
        desc="desc",
        author="author",
        homepage="https://v2.nonebot.dev",
        tags=json.dumps([{"label": "test", "color": "#ffffff"}]),
        is_official=False,
    )

    assert (
        info.validation_message
        == """> Bot: name\n\n**✅ 所有测试通过，一切准备就绪!**\n\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff</li><li>✅ 项目 <a href="https://v2.nonebot.dev">主页</a> 返回状态码 200.</li></code></pre></details>"""
    )

    calls = [
        mocker.call("https://v2.nonebot.dev"),
    ]
    mock_requests.assert_has_calls(calls)


def test_bot_info_validation_failed(mocker: MockerFixture) -> None:
    """测试验证失败的情况"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)
    mock_issue: Issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body(
        homepage="https://www.baidu.com",
        tags=[
            {"label": "test", "color": "#ffffff"},
            {"label": "testtoolong", "color": "#fffffff"},
        ],
    )
    mock_issue.user.login = "author"

    try:
        info = BotPublishInfo.from_issue(mock_issue)
    except MyValidationError as e:
        assert (
            e.message
            == """> Bot: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题:**\n<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保您的项目主页可访问。</dt></li><li>⚠️ 第 2 个标签名称过长<dt>请确保标签名称不超过 10 个字符。</dt></li><li>⚠️ 第 2 个标签颜色错误<dt>请确保标签颜色符合十六进制颜色码规则。</dt></li></code></pre>"""
        )

    calls = [
        mocker.call("https://www.baidu.com"),
    ]
    mock_requests.assert_has_calls(calls)


def test_bot_info_validation_failed_json_error(mocker: MockerFixture) -> None:
    """测试验证失败的情况，JSON 解析错误"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)
    mock_issue: Issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body(
        homepage="https://www.baidu.com",
        tags="not a json",
    )
    mock_issue.user.login = "author"

    try:
        info = BotPublishInfo.from_issue(mock_issue)
    except MyValidationError as e:
        assert (
            e.message
            == """> Bot: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题:**\n<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保您的项目主页可访问。</dt></li><li>⚠️ 标签解码失败。<dt>请确保标签格式正确。</dt></li></code></pre>"""
        )

    calls = [
        mocker.call("https://www.baidu.com"),
    ]
    mock_requests.assert_has_calls(calls)


def test_bot_info_validation_failed_tag_field_missing(mocker: MockerFixture) -> None:
    """测试验证失败的情况，tag 字段缺失"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)
    mock_issue: Issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body(
        homepage="https://www.baidu.com",
        tags=[{"label": "test"}],
    )
    mock_issue.user.login = "author"

    try:
        info = BotPublishInfo.from_issue(mock_issue)
    except MyValidationError as e:
        assert (
            e.message
            == """> Bot: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题:**\n<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保您的项目主页可访问。</dt></li><li>⚠️ 第 1 个标签缺少 color 字段。<dt>请确保标签字段完整。</dt></li></code></pre>"""
        )

    calls = [
        mocker.call("https://www.baidu.com"),
    ]
    mock_requests.assert_has_calls(calls)


def test_bot_info_validation_failed_name_tags_missing(mocker: MockerFixture) -> None:
    """测试验证失败的情况，name, tags 字段缺失"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)
    mock_issue: Issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body(name="", tags="")
    mock_issue.user.login = "author"

    try:
        info = BotPublishInfo.from_issue(mock_issue)
    except MyValidationError as e:
        assert (
            e.message
            == """> Bot: \n\n**⚠️ 在发布检查过程中，我们发现以下问题:**\n<pre><code><li>⚠️ name: 无法匹配到数据。<dt>请确保填写该项目。</dt></li><li>⚠️ tags: 无法匹配到数据。<dt>请确保填写该项目。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 项目 <a href="https://v2.nonebot.dev">主页</a> 返回状态码 200.</li></code></pre></details>"""
        )

    calls = [
        mocker.call("https://v2.nonebot.dev"),
    ]
    mock_requests.assert_has_calls(calls)
