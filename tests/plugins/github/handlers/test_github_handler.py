import pytest
from githubkit.rest import Issue
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


async def test_get_pull_request_by_branch(app: App, mocker: MockerFixture) -> None:
    """测试根据分支名称获取拉取请求"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_pull = mocker.MagicMock()
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

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
                    0: {"owner": "owner", "repo": "repo", "head": "owner:branch"},
                }
            ),
        )
        pull = await github_handler.get_pull_request_by_branch("branch")
        assert pull == mock_pull


async def test_get_pull_request_by_branch_empty(
    app: App, mocker: MockerFixture
) -> None:
    """测试根据分支名称获取拉取请求，为空的情况"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

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
                    0: {"owner": "owner", "repo": "repo", "head": "owner:branch"},
                }
            ),
        )
        with pytest.raises(ValueError, match="找不到分支 branch 对应的拉取请求"):
            await github_handler.get_pull_request_by_branch("branch")


async def test_get_pull_request(app: App, mocker: MockerFixture) -> None:
    """测试获取拉取请求"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_pull = mocker.MagicMock()
    mock_pull_resp = mocker.MagicMock()
    mock_pull_resp.parsed_data = mock_pull

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
                    api="rest.pulls.async_get",
                    result=mock_pull_resp,
                ),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "pull_number": 123},
                }
            ),
        )
        pull = await github_handler.get_pull_request(123)
        assert pull == mock_pull


async def test_draft_pull_request(app: App, mocker: MockerFixture) -> None:
    """测试将拉取请求标记为草稿"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_pull = mocker.MagicMock()
    mock_pull.draft = False
    mock_pull.node_id = 123
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

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
                    api="rest.pulls.async_list",
                    result=mock_pulls_resp,
                ),
                GitHubApi(api="async_graphql", result=None),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "head": "owner:branch"},
                    1: {
                        "query": """\
mutation convertPullRequestToDraft($pullRequestId: ID!) {
                    convertPullRequestToDraft(input: {pullRequestId: $pullRequestId}) {
                        clientMutationId
                    }
                }\
""",
                        "variables": {
                            "pullRequestId": 123,
                        },
                    },
                }
            ),
        )
        await github_handler.draft_pull_request("branch")


async def test_draft_pull_request_no_pr(app: App, mocker: MockerFixture) -> None:
    """测试将拉取请求标记为草稿，但是没有对应的拉取请求"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

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
                    api="rest.pulls.async_list",
                    result=mock_pulls_resp,
                ),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "head": "owner:branch"},
                }
            ),
        )
        await github_handler.draft_pull_request("branch")


async def test_draft_pull_request_drafted(app: App, mocker: MockerFixture) -> None:
    """测试将拉取请求标记为草稿，但已经是草稿的情况"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_pull = mocker.MagicMock()
    mock_pull.draft = True
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

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
                    api="rest.pulls.async_list",
                    result=mock_pulls_resp,
                ),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "head": "owner:branch"},
                }
            ),
        )
        await github_handler.draft_pull_request("branch")


async def test_merge_pull_request(app: App, mocker: MockerFixture) -> None:
    """测试合并拉取请求"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_pull = mocker.MagicMock()
    mock_pull_resp = mocker.MagicMock()
    mock_pull_resp.parsed_data = mock_pull

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
                    api="rest.pulls.async_merge",
                    result=mock_pull,
                ),
            ],
            snapshot(
                {
                    0: {
                        "owner": "owner",
                        "repo": "repo",
                        "pull_number": 123,
                        "merge_method": "rebase",
                    },
                }
            ),
        )
        await github_handler.merge_pull_request(123, "rebase")


async def test_update_pull_request_status(app: App, mocker: MockerFixture) -> None:
    """测试更新拉取请求状态"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_pull = mocker.MagicMock()
    mock_pull.title = "old title"
    mock_pull.draft = True
    mock_pull.number = 111
    mock_pull.node_id = 222
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

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
                GitHubApi(api="rest.pulls.async_update", result=None),
                GitHubApi(api="async_graphql", result=None),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "head": "owner:branch"},
                    1: {
                        "owner": "owner",
                        "repo": "repo",
                        "pull_number": 111,
                        "title": "new title",
                    },
                    2: {
                        "query": """\
mutation markPullRequestReadyForReview($pullRequestId: ID!) {
                        markPullRequestReadyForReview(input: {pullRequestId: $pullRequestId}) {
                            clientMutationId
                        }
                    }\
""",
                        "variables": {"pullRequestId": 222},
                    },
                }
            ),
        )
        await github_handler.update_pull_request_status("new title", "branch")


async def test_create_pull_request(app: App, mocker: MockerFixture) -> None:
    """测试创建拉取请求"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_pull = mocker.MagicMock()
    mock_pull.number = 123
    mock_pull_resp = mocker.MagicMock()
    mock_pull_resp.parsed_data = mock_pull

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )
        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.pulls.async_create", result=mock_pull_resp),
            ],
            snapshot(
                {
                    0: {
                        "owner": "owner",
                        "repo": "repo",
                        "title": "new title",
                        "body": "new body",
                        "base": "main",
                        "head": "branch",
                    },
                }
            ),
        )
        number = await github_handler.create_pull_request(
            "main", "new title", "branch", "new body"
        )
        assert number == 123


async def test_add_labels(app: App) -> None:
    """测试添加标签"""
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
                GitHubApi(api="rest.issues.async_add_labels", result=True),
            ],
            snapshot(
                {
                    0: {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                        "labels": ["Publish", "Plugin"],
                    },
                }
            ),
        )
        await github_handler.add_labels(76, ["Publish", "Plugin"])


async def test_ready_pull_request(app: App) -> None:
    """测试标记拉取请求为可评审"""
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
                GitHubApi(api="async_graphql", result=None),
            ],
            snapshot(
                {
                    0: {
                        "query": """\
mutation markPullRequestReadyForReview($pullRequestId: ID!) {
                        markPullRequestReadyForReview(input: {pullRequestId: $pullRequestId}) {
                            clientMutationId
                        }
                    }\
""",
                        "variables": {"pullRequestId": "node_id"},
                    },
                }
            ),
        )
        await github_handler.ready_pull_request("node_id")


async def test_update_pull_request_title(app: App) -> None:
    """测试修改拉取请求标题"""
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
                GitHubApi(api="rest.pulls.async_update", result=True),
            ],
            snapshot(
                {
                    0: {
                        "owner": "owner",
                        "repo": "repo",
                        "pull_number": 123,
                        "title": "new title",
                    },
                }
            ),
        )
        await github_handler.update_pull_request_title("new title", 123)


async def test_get_user_name(app: App, mocker: MockerFixture) -> None:
    """测试获取用户名"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_user = mocker.MagicMock()
    mock_user.login = "name"
    mock_user_resp = mocker.MagicMock()
    mock_user_resp.parsed_data = mock_user

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.users.async_get_by_id", result=mock_user_resp),
            ],
            snapshot(
                {
                    0: {"account_id": 1},
                }
            ),
        )
        await github_handler.get_user_name(1)


async def test_get_user_id(app: App, mocker: MockerFixture) -> None:
    """测试获取用户 ID"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_user = mocker.MagicMock()
    mock_user.id = "1"
    mock_user_resp = mocker.MagicMock()
    mock_user_resp.parsed_data = mock_user

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
                    api="rest.users.async_get_by_username", result=mock_user_resp
                ),
            ],
            snapshot(
                {
                    0: {"username": "name"},
                }
            ),
        )
        await github_handler.get_user_id("name")


async def test_get_issue(app: App, mocker: MockerFixture) -> None:
    """测试获取议题"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.models import RepoInfo

    mock_issue = mocker.MagicMock()
    mock_issue_resp = mocker.MagicMock()
    mock_issue_resp.parsed_data = mock_issue

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.issues.async_get", result=mock_issue_resp),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "issue_number": 123},
                }
            ),
        )
        issue = await github_handler.get_issue(123)
        assert issue == mock_issue


async def test_close_issue(app: App) -> None:
    """测试关闭议题"""
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
                        "issue_number": 123,
                        "state": "closed",
                        "state_reason": "completed",
                    },
                }
            ),
        )
        await github_handler.close_issue("completed", 123)


async def test_to_issue_handler(app: App, mocker: MockerFixture) -> None:
    """测试获取议题处理器"""
    from src.plugins.github.handlers.github import GithubHandler
    from src.plugins.github.handlers.issue import IssueHandler
    from src.plugins.github.models import RepoInfo

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue_resp = mocker.MagicMock()
    mock_issue_resp.parsed_data = mock_issue

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        github_handler = GithubHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.issues.async_get", result=mock_issue_resp),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "issue_number": 123},
                }
            ),
        )
        issue_handler = await github_handler.to_issue_handler(123)
        assert isinstance(issue_handler, IssueHandler)
        assert issue_handler.issue == mock_issue
