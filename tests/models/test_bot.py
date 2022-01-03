# type: ignore
import json
from collections import OrderedDict

from github.Issue import Issue
from pytest_mock import MockerFixture

from src.models import BotPublishInfo


def generate_issue_body(
    name: str = "name",
    desc: str = "desc",
    homepage: str = "https://v2.nonebot.dev",
    tags: list = [{"label": "test", "color": "#ffffff"}],
):
    return f"""**机器人名称：**\n\n{name}\n\n**机器人功能：**\n\n{desc}\n\n**机器人项目仓库/主页链接：**\n\n{homepage}\n\n**标签：**\n\n{json.dumps(tags)}"""


def test_bot_info() -> None:
    info = BotPublishInfo(
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )

    assert OrderedDict(info.dict()) == OrderedDict(
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )


def test_bot_from_issue(mocker: MockerFixture) -> None:
    """测试从 issue 中构造 BotPublishInfo"""
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


def test_bot_from_issue_trailing_whitespace(mocker: MockerFixture) -> None:
    """测试末尾如果有空格的情况"""
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


def mocked_requests_get(url: str):
    class MockResponse:
        def __init__(self, status_code: int):
            self.status_code = status_code

    if url == "https://pypi.org/pypi/project_link/json":
        return MockResponse(200)
    if url == "https://v2.nonebot.dev":
        return MockResponse(200)

    return MockResponse(404)


def test_bot_info_validation_success(mocker: MockerFixture) -> None:
    """测试验证成功的情况"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)

    info = BotPublishInfo(
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
        == """> Bot: name\n\n**✅ All tests passed, you are ready to go!**\n\n<details><summary>Report Detail</summary><pre><code><li>✅ Project <a href="https://v2.nonebot.dev">homepage</a> returns 200.</li></code></pre></details>"""
    )

    calls = [
        mocker.call("https://v2.nonebot.dev"),
    ]
    mock_requests.assert_has_calls(calls)


def test_bot_info_validation_failed(mocker: MockerFixture) -> None:
    """测试验证失败的情况"""
    mock_requests = mocker.patch("requests.get", side_effect=mocked_requests_get)

    info = BotPublishInfo(
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
        == """> Bot: name\n\n**⚠️ We have found following problem(s) in pre-publish progress:**\n<pre><code><li>⚠️ Project <a href="https://www.baidu.com">homepage</a> returns 404.<dt>Please make sure that your project has a publicly visible homepage.</dt></li></code></pre>"""
    )

    calls = [
        mocker.call("https://www.baidu.com"),
    ]
    mock_requests.assert_has_calls(calls)
