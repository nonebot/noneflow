from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockerFixture

from tests.plugins.github.utils import MockBody, MockIssue, get_github_bot


async def test_ensure_issue_plugin_test_button(app: App, mocker: MockerFixture):
    """确保添加插件测试按钮"""
    from src.plugins.github.models import IssueHandler, RepoInfo
    from src.plugins.github.plugins.publish.utils import (
        ensure_issue_plugin_test_button,
    )

    mock_issue = MockIssue(
        body=MockBody(type="plugin").generate(),
        number=1,
    ).as_mock(mocker)

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "owner",
                    "repo": "repo",
                    "issue_number": 1,
                    "body": """\
### PyPI 项目名

project_link

### 插件 import 包名

module_name

### 标签

[{"label": "test", "color": "#ffffff"}]

### 插件配置项

```dotenv
log_level=DEBUG
```

### 插件测试

- [ ] 如需重新运行插件测试，请勾选左侧勾选框\
""",
                }
            ),
            True,
        )

        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        await ensure_issue_plugin_test_button(handler)


async def test_ensure_issue_plugin_test_button_checked(app: App, mocker: MockerFixture):
    """如果测试按钮勾选，则自动取消勾选"""
    from src.plugins.github.models import IssueHandler, RepoInfo
    from src.plugins.github.plugins.publish.utils import (
        ensure_issue_plugin_test_button,
    )

    mock_issue = MockIssue(
        body=MockBody(type="plugin", test_button=True).generate(),
        number=1,
    ).as_mock(mocker)

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "owner",
                    "repo": "repo",
                    "issue_number": 1,
                    "body": """\
### PyPI 项目名

project_link

### 插件 import 包名

module_name

### 标签

[{"label": "test", "color": "#ffffff"}]

### 插件配置项

```dotenv
log_level=DEBUG
```

### 插件测试

- [ ] 如需重新运行插件测试，请勾选左侧勾选框\
""",
                }
            ),
            True,
        )

        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        await ensure_issue_plugin_test_button(handler)


async def test_ensure_issue_plugin_test_button_unchecked(
    app: App, mocker: MockerFixture
):
    """如果测试按钮未勾选，则不进行操作"""
    from src.plugins.github.models import IssueHandler, RepoInfo
    from src.plugins.github.plugins.publish.utils import (
        ensure_issue_plugin_test_button,
    )

    mock_issue = MockIssue(
        body=MockBody(type="plugin", test_button=False).generate(),
        number=1,
    ).as_mock(mocker)

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        await ensure_issue_plugin_test_button(handler)


async def test_ensure_issue_plugin_test_button_in_progress(
    app: App, mocker: MockerFixture
):
    """确保添加插件测试按钮"""
    from src.plugins.github.models import IssueHandler, RepoInfo
    from src.plugins.github.plugins.publish.utils import (
        ensure_issue_plugin_test_button_in_progress,
    )

    mock_issue = MockIssue(
        body=MockBody(type="plugin").generate(),
        number=1,
    ).as_mock(mocker)

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)

        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "owner",
                    "repo": "repo",
                    "issue_number": 1,
                    "body": """\
### PyPI 项目名

project_link

### 插件 import 包名

module_name

### 标签

[{"label": "test", "color": "#ffffff"}]

### 插件配置项

```dotenv
log_level=DEBUG
```

### 插件测试

- [x] 🔥插件测试中，请稍后\
""",
                }
            ),
            True,
        )

        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        await ensure_issue_plugin_test_button_in_progress(handler)
