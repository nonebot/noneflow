from collections import OrderedDict

import requests
from github.Issue import Issue
from pytest_mock import MockerFixture

from src.models import PluginPublishInfo


def test_plugin_info() -> None:
    info = PluginPublishInfo(
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


def test_plugin_from_issue(mocker: MockerFixture) -> None:
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

    info = PluginPublishInfo.from_issue(mock_issue)

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


def test_plugin_info_valid(mocker: MockerFixture) -> None:
    mocker.patch("requests.get", return_value=mocker.MagicMock(status_code=200))  # type: ignore

    info = PluginPublishInfo(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
    )

    assert info.is_valid
    assert info.validation_message

    calls = [  # type: ignore
        mocker.call("https://pypi.org/pypi/project_link/json"),  # type: ignore
        mocker.call("https://www.baidu.com"),  # type: ignore
    ]
    requests.get.assert_has_calls(calls)  # type: ignore
