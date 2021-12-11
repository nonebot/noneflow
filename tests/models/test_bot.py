from collections import OrderedDict

import requests
from github.Issue import Issue
from pytest_mock import MockerFixture

from src.models import BotPublishInfo


def test_bot_info() -> None:
    info = BotPublishInfo(
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
    )

    assert OrderedDict(info.dict()) == OrderedDict(
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
    )


def test_bot_from_issue(mocker: MockerFixture) -> None:
    body = """
        <!-- DO NOT EDIT ! -->
        <!--
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

    info = BotPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict()) == OrderedDict(
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
    )


def test_bot_info_valid(mocker: MockerFixture) -> None:
    mocker.patch("requests.get", return_value=mocker.MagicMock(status_code=200))  # type: ignore

    info = BotPublishInfo(
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
    )

    assert info.is_valid
    assert (
        info.validation_message
        == """> Bot: name\n\n**✅ All tests passed, you are ready to go!**\n<details><summary>Report Detail</summary><pre><code><li>✅ Project <a href="https://www.baidu.com">homepage</a> returns 200.</li></code></pre></details>"""
    )

    calls = [  # type: ignore
        mocker.call("https://www.baidu.com"),  # type: ignore
    ]
    requests.get.assert_has_calls(calls)  # type: ignore
