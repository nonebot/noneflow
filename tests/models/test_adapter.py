from collections import OrderedDict

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
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
        module_name="module_name",
        project_link="project_link",
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
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
        module_name="module_name",
        project_link="project_link",
    )
