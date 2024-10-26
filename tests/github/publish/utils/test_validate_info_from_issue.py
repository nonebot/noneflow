from githubkit.rest import Issue
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.github.utils import (
    generate_issue_body_adapter,
    generate_issue_body_bot,
    generate_issue_body_plugin_skip_test,
    get_github_bot,
)


async def test_validate_info_from_issue_adapter(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    from src.plugins.github.plugins.publish.validation import (
        validate_adapter_info_from_issue,
    )

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_adapter()
    mock_issue.user.login = "test"

    result = await validate_adapter_info_from_issue(mock_issue)

    assert result.valid
    assert mocked_api["homepage"].called


async def test_validate_info_from_issue_bot(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    from src.plugins.github.plugins.publish.validation import (
        validate_bot_info_from_issue,
    )

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_bot()
    mock_issue.user.login = "test"

    result = await validate_bot_info_from_issue(mock_issue)

    assert result.valid
    assert mocked_api["homepage"].called


async def test_validate_info_from_issue_plugin(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    from src.plugins.github.models import RepoInfo
    from src.plugins.github.models.issue import IssueHandler
    from src.plugins.github.plugins.publish.validation import (
        validate_plugin_info_from_issue,
    )

    mock_user = mocker.MagicMock()
    mock_user.login = "test"
    mock_user.id = 1

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.body = generate_issue_body_plugin_skip_test()
    mock_issue.number = 1
    mock_issue.user = mock_user

    mock_comment = mocker.MagicMock()
    mock_comment.body = "/skip"
    mock_comment.author_association = "MEMBER"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)
        handler = IssueHandler(
            bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"), issue=mock_issue
        )

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "repo", "issue_number": 1},
            mock_list_comments_resp,
        )

        result = await validate_plugin_info_from_issue(mock_issue, handler)

    assert result.valid
    assert mocked_api["homepage"].called
