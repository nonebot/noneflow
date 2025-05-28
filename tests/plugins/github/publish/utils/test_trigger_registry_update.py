from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockerFixture

from tests.plugins.github.utils import (
    MockBody,
    MockIssue,
    get_github_bot,
    should_call_apis,
)


async def test_trigger_registry_update(app: App, mocker: MockerFixture):
    from src.plugins.github.constants import NONEFLOW_MARKER
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.utils import trigger_registry_update
    from src.providers.models import RepoInfo

    mock_issue = MockIssue(
        body=MockBody(type="plugin").generate(),
        number=1,
    ).as_mock(mocker)

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_bot_comment = mocker.MagicMock()
    mock_bot_comment.body = f"""
<details>\n<summary>历史测试</summary>
<pre><code>
<li>⚠️ <a href="https://github.com/nonebot/nonebot2/actions/runs/1">2025-03-28 02:21:18 CST</a>。</li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/2">2025-03-28 02:21:18 CST</a>。</li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/3">2025-03-28 02:22:18 CST</a>。</li><li>⚠️ <a href="https://github.com/nonebot/nonebot2/actions/runs/4">2025-03-28 02:22:18 CST</a>。</li>
</code></pre>
</details>
{NONEFLOW_MARKER}
"""

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment, mock_bot_comment]

    mock_artifact = mocker.MagicMock()
    mock_artifact.name = "noneflow"
    mock_artifact.id = 233

    mock_list_artifacts_data = mocker.MagicMock()
    mock_list_artifacts_data.total_count = 1
    mock_list_artifacts_data.artifacts = [mock_artifact]

    mock_list_artifacts_resp = mocker.MagicMock()
    mock_list_artifacts_resp.parsed_data = mock_list_artifacts_data

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        should_call_apis(
            ctx,
            [
                {
                    "api": "rest.issues.async_list_comments",
                    "result": mock_list_comments_resp,
                },
                {
                    "api": "rest.actions.async_list_workflow_run_artifacts",
                    "result": mock_list_artifacts_resp,
                },
                {
                    "api": "rest.repos.async_create_dispatch_event",
                    "result": True,
                },
            ],
            [
                {"owner": "owner", "repo": "registry", "issue_number": 1},
                {"owner": "owner", "repo": "registry", "run_id": 3},
                snapshot(
                    {
                        "repo": "registry",
                        "owner": "owner",
                        "event_type": "registry_update",
                        "client_payload": {
                            "repo_info": {"owner": "owner", "repo": "registry"},
                            "artifact_id": 233,
                        },
                    }
                ),
            ],
        )

        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="registry"),
            issue=mock_issue,
        )
        await trigger_registry_update(handler)


async def test_trigger_registry_update_missing_comment(app: App, mocker: MockerFixture):
    """如果没有找到对应的评论，则不触发更新"""
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.utils import trigger_registry_update
    from src.providers.models import RepoInfo

    mock_issue = MockIssue(
        body=MockBody(type="plugin").generate(),
        number=1,
    ).as_mock(mocker)

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        should_call_apis(
            ctx,
            [
                {
                    "api": "rest.issues.async_list_comments",
                    "result": mock_list_comments_resp,
                },
            ],
            [
                {"owner": "owner", "repo": "registry", "issue_number": 1},
            ],
        )

        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="registry"),
            issue=mock_issue,
        )
        await trigger_registry_update(handler)


async def test_trigger_registry_update_missing_artifact(
    app: App, mocker: MockerFixture
):
    """如果没有找到对应的 artifact，则不触发更新"""
    from src.plugins.github.constants import NONEFLOW_MARKER
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.utils import trigger_registry_update
    from src.providers.models import RepoInfo

    mock_issue = MockIssue(
        body=MockBody(type="plugin").generate(),
        number=1,
    ).as_mock(mocker)

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_bot_comment = mocker.MagicMock()
    mock_bot_comment.body = f"""
<details>\n<summary>历史测试</summary>
<pre><code>
<li>⚠️ <a href="https://github.com/nonebot/nonebot2/actions/runs/1">2025-03-28 02:21:18 CST</a>。</li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/2">2025-03-28 02:21:18 CST</a>。</li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/3">2025-03-28 02:22:18 CST</a>。</li><li>⚠️ <a href="https://github.com/nonebot/nonebot2/actions/runs/4">2025-03-28 02:22:18 CST</a>。</li>
</code></pre>
</details>
{NONEFLOW_MARKER}
"""

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment, mock_bot_comment]

    mock_artifact = mocker.MagicMock()
    mock_artifact.name = "test"
    mock_artifact.id = 233

    mock_list_artifacts_data = mocker.MagicMock()
    mock_list_artifacts_data.total_count = 1
    mock_list_artifacts_data.artifacts = [mock_artifact]

    mock_list_artifacts_resp = mocker.MagicMock()
    mock_list_artifacts_resp.parsed_data = mock_list_artifacts_data

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        should_call_apis(
            ctx,
            [
                {
                    "api": "rest.issues.async_list_comments",
                    "result": mock_list_comments_resp,
                },
                {
                    "api": "rest.actions.async_list_workflow_run_artifacts",
                    "result": mock_list_artifacts_resp,
                },
            ],
            [
                {"owner": "owner", "repo": "registry", "issue_number": 1},
                {"owner": "owner", "repo": "registry", "run_id": 3},
            ],
        )

        handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="registry"),
            issue=mock_issue,
        )
        await trigger_registry_update(handler)
