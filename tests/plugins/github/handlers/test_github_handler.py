from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockerFixture

from tests.plugins.github.utils import GitHubApi, get_github_bot, should_call_apis


async def test_update_issue_title(app: App) -> None:
    """测试修改议题标题"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.issues.async_update", result=True),
            ],
            snapshot(
                {
                    0: {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                        "title": "new title",
                    },
                }
            ),
        )
        await github_handler.update_issue_title("new title", 76)


async def test_update_issue_body(app: App) -> None:
    """测试更新议题内容"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.issues.async_update", result=True),
            ],
            snapshot(
                {
                    0: {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                        "body": "new body",
                    },
                }
            ),
        )
        await github_handler.update_issue_body("new body", 76)


async def test_create_dispatch_event(app: App) -> None:
    """测试创建触发事件"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.repos.async_create_dispatch_event", result=True),
            ],
            snapshot(
                {
                    0: {
                        "owner": "owner",
                        "repo": "repo",
                        "event_type": "event",
                        "client_payload": {"key": "value"},
                    },
                }
            ),
        )
        await github_handler.create_dispatch_event("event", {"key": "value"})


async def test_list_comments(app: App, mocker: MockerFixture) -> None:
    """测试拉取所有评论"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = []

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments", result=mock_comments_resp
                ),
            ],
            snapshot(
                {
                    0: {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                    },
                }
            ),
        )
        await github_handler.list_comments(76)


async def test_create_comment(app: App) -> None:
    """测试发布评论"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.issues.async_create_comment", result=True),
            ],
            snapshot(
                {
                    0: {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                        "body": "new comment",
                    },
                }
            ),
        )
        await github_handler.create_comment("new comment", 76)


async def test_update_comment(app: App) -> None:
    """测试修改评论"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.issues.async_update_comment", result=True),
            ],
            snapshot(
                {
                    0: {
                        "owner": "owner",
                        "repo": "repo",
                        "comment_id": 123,
                        "body": "updated comment",
                    },
                }
            ),
        )
        await github_handler.update_comment(123, "updated comment")


async def test_comment_issue(app: App, mocker: MockerFixture) -> None:
    """测试发布评论"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = []

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments", result=mock_comments_resp
                ),
                GitHubApi(api="rest.issues.async_create_comment", result=True),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "issue_number": 76},
                    1: {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                        "body": "new comment",
                    },
                }
            ),
        )
        await github_handler.comment_issue("new comment", 76)


async def test_comment_issue_reuse(app: App, mocker: MockerFixture) -> None:
    """测试发布评论，复用的情况"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_comment = mocker.MagicMock()
    mock_comment.body = "old comment\n<!-- NONEFLOW -->"
    mock_comment.id = 123
    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments", result=mock_comments_resp
                ),
                GitHubApi(api="rest.issues.async_update_comment", result=True),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "issue_number": 76},
                    1: {
                        "owner": "owner",
                        "repo": "repo",
                        "comment_id": 123,
                        "body": "new comment",
                    },
                }
            ),
        )
        await github_handler.comment_issue("new comment", 76)


async def test_comment_issue_reuse_no_change(app: App, mocker: MockerFixture) -> None:
    """测试发布评论，复用且无变化的情况"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_comment = mocker.MagicMock()
    mock_comment.body = "comment\n<!-- NONEFLOW -->"
    mock_comment.id = 123
    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments", result=mock_comments_resp
                ),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "issue_number": 76},
                }
            ),
        )
        await github_handler.comment_issue("comment\n<!-- NONEFLOW -->", 76)


async def test_get_pull_requests_by_label(app: App, mocker: MockerFixture) -> None:
    """测试获取指定标签下的所有 PR"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_label_plugin = mocker.MagicMock()
    mock_label_plugin.name = "Plugin"
    mock_label_bot = mocker.MagicMock()
    mock_label_bot.name = "Bot"

    mock_pull_bot = mocker.MagicMock()
    mock_pull_bot.labels = [mock_label_bot]
    mock_pull_plugin = mocker.MagicMock()
    mock_pull_plugin.labels = [mock_label_plugin]

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull_bot, mock_pull_plugin]

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.pulls.async_list", result=mock_pulls_resp),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "state": "open"},
                }
            ),
        )
        pulls = await github_handler.get_pull_requests_by_label("Plugin")
        assert pulls == [mock_pull_plugin]
