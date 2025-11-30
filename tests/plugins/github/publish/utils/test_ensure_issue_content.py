from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockerFixture

from tests.plugins.github.utils import (
    MockIssue,
    get_github_bot,
)


async def test_ensure_issue_content(app: App, mocker: MockerFixture):
    """确保议题内容完整"""
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.utils import ensure_issue_content
    from src.providers.models import RepoInfo

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)
        issue = MockIssue(body="什么都没有", number=1)
        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=issue.as_mock(mocker),
        )

        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "owner",
                "repo": "repo",
                "issue_number": 1,
                "body": snapshot(
                    """\
### 插件名称

### 插件描述

### 插件项目仓库/主页链接

### 插件类型

### 插件支持的适配器

什么都没有\
"""
                ),
            },
            True,
        )

        await ensure_issue_content(handler)


async def test_ensure_issue_content_partial(app: App, mocker: MockerFixture):
    """确保议题内容被补全"""
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.utils import ensure_issue_content
    from src.providers.models import RepoInfo

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)

        issue = MockIssue(body="### 插件名称\n\nname\n\n### 插件类型\n", number=1)
        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=issue.as_mock(mocker),
        )

        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "owner",
                "repo": "repo",
                "issue_number": 1,
                "body": "### 插件描述\n\n### 插件项目仓库/主页链接\n\n### 插件支持的适配器\n\n### 插件名称\n\nname\n\n### 插件类型\n",
            },
            True,
        )

        await ensure_issue_content(handler)


async def test_ensure_issue_content_complete(app: App, mocker: MockerFixture):
    """确保议题内容已经补全之后不会再次补全"""
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.utils import ensure_issue_content
    from src.providers.models import RepoInfo

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)
        issue = MockIssue(
            body="### 插件描述\n\n### 插件项目仓库/主页链接\n\n### 插件支持的适配器\n\n### 插件名称\n\nname\n\n### 插件类型\n",
            number=1,
        )
        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=issue.as_mock(mocker),
        )

        await ensure_issue_content(handler)
