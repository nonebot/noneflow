from unittest.mock import _Call, call

from githubkit.rest import Issue
from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockerFixture

from tests.plugins.github.utils import GitHubApi, get_github_bot, should_call_apis


async def test_issue_property(app: App, mocker: MockerFixture) -> None:
    """测试获取 IssueHandler 的属性"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import AuthorInfo, RepoInfo

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 111
    mock_issue.user = mocker.MagicMock()
    mock_issue.user.login = "he0119"
    mock_issue.user.id = 1

    mock_pull = mocker.MagicMock()
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        assert issue_handler.issue_number == 111
        assert issue_handler.author_info == AuthorInfo(author="he0119", author_id=1)
        assert issue_handler.author == "he0119"
        assert issue_handler.author_id == 1


async def test_update_issue_title(app: App, mocker: MockerFixture) -> None:
    """测试修改议题标题"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76
    mock_issue.title = "old title"

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.issues.async_update", result=True),
            ],
            snapshot(
                [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                        "title": "new title",
                    },
                ]
            ),
        )
        await issue_handler.update_issue_title("new title")
        assert mock_issue.title == "new title"
        # 再次修改，但标题一致，不会调用 API
        await issue_handler.update_issue_title("new title")


async def test_update_issue_body(app: App, mocker: MockerFixture) -> None:
    """测试更新议题内容"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76
    mock_issue.body = "old body"

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.issues.async_update", result=True),
            ],
            snapshot(
                [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                        "body": "new body",
                    },
                ]
            ),
        )
        await issue_handler.update_issue_body("new body")
        assert mock_issue.body == "new body"
        # 再次修改，但内容一致，不会调用 API
        await issue_handler.update_issue_body("new body")


async def test_close_issue(app: App, mocker: MockerFixture) -> None:
    """测试关闭议题"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 123
    mock_issue.state = "open"

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.issues.async_update", result=True),
            ],
            snapshot(
                [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 123,
                        "state": "closed",
                        "state_reason": "completed",
                    },
                ]
            ),
        )
        await issue_handler.close_issue("completed")


async def test_create_pull_request(app: App, mocker: MockerFixture) -> None:
    """测试创建拉取请求"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_pull = mocker.MagicMock()
    mock_pull.number = 123
    mock_pull_resp = mocker.MagicMock()
    mock_pull_resp.parsed_data = mock_pull

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )
        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.pulls.async_create", result=mock_pull_resp),
            ],
            snapshot(
                [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "title": "new title",
                        "body": "resolve #76",
                        "base": "main",
                        "head": "branch",
                    },
                ]
            ),
        )
        number = await issue_handler.create_pull_request("main", "new title", "branch")
        assert number == 123


async def test_list_comments(app: App, mocker: MockerFixture) -> None:
    """测试拉取所有评论"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = []

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments", result=mock_comments_resp
                ),
            ],
            snapshot(
                [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                    },
                ]
            ),
        )
        await issue_handler.list_comments()


async def test_comment_issue(app: App, mocker: MockerFixture) -> None:
    """测试发布评论"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = []

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
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
                [
                    {"owner": "owner", "repo": "repo", "issue_number": 76},
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                        "body": "new comment",
                    },
                ]
            ),
        )
        await issue_handler.resuable_comment_issue("new comment")


async def test_should_skip_test(app: App, mocker: MockerFixture) -> None:
    """测试是否应该跳过测试"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = []

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments", result=mock_comments_resp
                ),
            ],
            snapshot(
                [
                    {"owner": "owner", "repo": "repo", "issue_number": 76},
                ]
            ),
        )
        assert await issue_handler.should_skip_test() is False


async def test_should_skip_test_true(app: App, mocker: MockerFixture) -> None:
    """测试是否应该跳过测试，应该跳过"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    mock_comment = mocker.MagicMock()
    mock_comment.author_association = "OWNER"
    mock_comment.body = "/skip"

    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments", result=mock_comments_resp
                ),
            ],
            snapshot(
                [
                    {"owner": "owner", "repo": "repo", "issue_number": 76},
                ]
            ),
        )
        assert await issue_handler.should_skip_test() is True


async def test_should_skip_test_not_admin(app: App, mocker: MockerFixture) -> None:
    """测试是否应该跳过测试，只是贡献者"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    mock_comment = mocker.MagicMock()
    mock_comment.author_association = "CONTRIBUTOR"
    mock_comment.body = "/skip"

    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments", result=mock_comments_resp
                ),
            ],
            snapshot(
                [
                    {"owner": "owner", "repo": "repo", "issue_number": 76},
                ]
            ),
        )
        assert await issue_handler.should_skip_test() is False


async def test_commit_and_push(app: App, mocker: MockerFixture) -> None:
    """测试提交并推送"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_run_shell_command = mocker.patch(
        "src.plugins.github.handlers.git.run_shell_command"
    )

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.user = mocker.MagicMock()
    mock_issue.user.login = "he0119"
    mock_issue.user.id = 1

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        issue_handler.commit_and_push("message", "main")

    mock_run_shell_command.assert_has_calls(
        [
            call(["git", "config", "--global", "user.name", "he0119"]),
            call(
                [
                    "git",
                    "config",
                    "--global",
                    "user.email",
                    "he0119@users.noreply.github.com",
                ]
            ),
            call(["git", "commit", "-m", "message"]),
            call(["git", "fetch", "origin"]),
            call(["git", "diff", "origin/main", "main"]),
            _Call(("().stdout.__bool__", (), {})),
            call(["git", "push", "origin", "main", "-f"]),
        ],
    )


async def test_get_self_comment(app: App, mocker: MockerFixture) -> None:
    """测试获取自己的评论"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_comment_bot = mocker.MagicMock()
    mock_comment_bot.body = "bot comment\n<!-- NONEFLOW -->"
    mock_comment_bot.id = 123

    mock_comment_user = mocker.MagicMock()
    mock_comment_user.body = "user comment"
    mock_comment_user.id = 456

    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = [mock_comment_user, mock_comment_bot]

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments", result=mock_comments_resp
                ),
            ],
            snapshot(
                [
                    {"owner": "owner", "repo": "repo", "issue_number": 76},
                ]
            ),
        )
        comment = await issue_handler.get_self_comment()
        assert comment == mock_comment_bot


async def test_get_self_comment_not_found(app: App, mocker: MockerFixture) -> None:
    """测试获取自己的评论，未找到的情况"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_comment_user = mocker.MagicMock()
    mock_comment_user.id = 123
    mock_comment_user.body = "bot comment"
    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = [mock_comment_user]

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments", result=mock_comments_resp
                ),
            ],
            snapshot(
                [
                    {"owner": "owner", "repo": "repo", "issue_number": 76},
                ]
            ),
        )
        comment = await issue_handler.get_self_comment()
        assert comment is None


async def test_comment_issue_new(app: App, mocker: MockerFixture) -> None:
    """测试发布新评论"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.issues.async_create_comment", result=True),
            ],
            snapshot(
                [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                        "body": "test comment",
                    },
                ]
            ),
        )
        await issue_handler.comment_issue("test comment")


async def test_comment_issue_update_existing(app: App, mocker: MockerFixture) -> None:
    """测试更新已存在的评论"""
    from src.plugins.github.handlers.issue import IssueHandler
    from src.providers.models import RepoInfo

    mock_comment = mocker.MagicMock()
    mock_comment.id = 123
    mock_comment.body = "old comment"

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(api="rest.issues.async_update_comment", result=True),
            ],
            snapshot(
                [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "comment_id": 123,
                        "body": "updated comment",
                    },
                ]
            ),
        )
        await issue_handler.comment_issue("updated comment", self_comment=mock_comment)
