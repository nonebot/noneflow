import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

from inline_snapshot import snapshot
from nonebot.adapters.github import PullRequestClosed
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.plugins.github.event import get_mock_event
from tests.plugins.github.resolve.utils import get_pr_labels
from tests.plugins.github.utils import (
    MockIssue,
    assert_subprocess_run_calls,
    generate_issue_body_bot,
    generate_issue_body_remove,
    get_github_bot,
    mock_subprocess_run_with_side_effect,
)


async def test_resolve_pull_request(
    app: App,
    mocker: MockerFixture,
    mock_installation: MagicMock,
    mock_installation_token: MagicMock,
    mocked_api: MockRouter,
    tmp_path: Path,
) -> None:
    """测试能正确处理拉取请求关闭后其他拉取请求的冲突问题"""
    from src.plugins.github.plugins.resolve import pr_close_matcher
    from src.providers.models import (
        REGISTRY_DATA_NAME,
        BotPublishInfo,
        Color,
        RegistryArtifactData,
        Tag,
    )

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_issue = MockIssue(
        body=generate_issue_body_remove(type="Bot"), number=76
    ).as_mock(mocker)
    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_publish_issue = MockIssue(body=generate_issue_body_bot(), number=100).as_mock(
        mocker
    )
    mock_publish_issue_resp = mocker.MagicMock()
    mock_publish_issue_resp.parsed_data = mock_publish_issue
    mock_publish_pull = mocker.MagicMock()
    mock_publish_pull.title = "Bot: test"
    mock_publish_pull.draft = False
    mock_publish_pull.head.ref = "publish/issue100"
    mock_publish_pull.labels = get_pr_labels(["Publish", "Bot"])

    mock_publish_issue_comment = mocker.MagicMock()
    mock_publish_issue_comment.body = """
<details>
<summary>历史测试</summary>
<pre><code>
<li>⚠️ <a href="https://github.com/owner/repo/actions/runs/14156878699">2025-03-28 02:21:18 CST</a></li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:21:18 CST</a></li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:22:18 CST</a>。</li><li>⚠️ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:22:18 CST</a></li>
</code></pre>
</details>
<!-- NONEFLOW -->
"""
    mock_publish_list_comments_resp = mocker.MagicMock()
    mock_publish_list_comments_resp.parsed_data = [mock_publish_issue_comment]

    mock_publish_artifact = mocker.MagicMock()
    mock_publish_artifact.name = "noneflow"
    mock_publish_artifact.id = 123456789
    mock_publish_artifacts = mocker.MagicMock()
    mock_publish_artifacts.artifacts = [mock_publish_artifact]
    mock_publish_artifact_resp = mocker.MagicMock()
    mock_publish_artifact_resp.parsed_data = mock_publish_artifacts

    raw_data = {
        "module_name": "module_name",
        "project_link": "project_link",
        "time": "2025-03-28T02:21:18Z",
        "version": "1.0.0",
        "name": "name",
        "desc": "desc",
        "author": "he0119",
        "author_id": 1,
        "homepage": "https://nonebot.dev",
        "tags": [Tag(label="test", color=Color("#ffffff"))],
        "is_official": False,
    }
    info = BotPublishInfo.model_construct(**raw_data)
    registry_data = RegistryArtifactData.from_info(info)

    # 创建 zip 文件内容
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 将 registry_data 转换为 JSON 字符串并添加到 zip 中
        json_content = registry_data.model_dump_json(indent=2)
        zip_file.writestr(REGISTRY_DATA_NAME, json_content)

    # 获取 zip 文件的字节内容
    publish_zip_content = zip_buffer.getvalue()

    mock_publish_download_artifact_resp = mocker.MagicMock()
    mock_publish_download_artifact_resp.content = publish_zip_content

    mock_remove_issue = MockIssue(
        body=generate_issue_body_remove(
            type="Bot", key="CoolQBot:https://github.com/he0119/CoolQBot"
        ),
        number=101,
    ).as_mock(mocker)
    mock_remove_issue_resp = mocker.MagicMock()
    mock_remove_issue_resp.parsed_data = mock_remove_issue
    mock_remove_pull = mocker.MagicMock()
    mock_remove_pull.title = "Bot: remove CoolQBot"
    mock_remove_pull.draft = False
    mock_remove_pull.head.ref = "remove/issue101"
    mock_remove_pull.labels = get_pr_labels(["Remove", "Bot"])

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_publish_pull, mock_remove_pull]

    async with app.test_matcher() as ctx:
        _adapter, bot = get_github_bot(ctx)

        event = get_mock_event(PullRequestClosed)
        event.payload.pull_request.labels = get_pr_labels(["Remove", "Bot"])
        event.payload.pull_request.merged = True

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            snapshot({"owner": "he0119", "repo": "action-test"}),
            mock_installation,
        )
        ctx.should_call_api(
            "rest.apps.async_create_installation_access_token",
            snapshot({"installation_id": mock_installation.parsed_data.id}),
            mock_installation_token,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            snapshot({"owner": "he0119", "repo": "action-test", "issue_number": 76}),
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 76,
                    "state": "closed",
                    "state_reason": "completed",
                }
            ),
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            snapshot({"owner": "he0119", "repo": "action-test", "state": "open"}),
            mock_pulls_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            snapshot({"owner": "he0119", "repo": "action-test", "issue_number": 100}),
            mock_publish_issue_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            snapshot({"owner": "he0119", "repo": "action-test", "issue_number": 100}),
            mock_publish_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.actions.async_list_workflow_run_artifacts",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "run_id": 14156878699,
                }
            ),
            mock_publish_artifact_resp,
        )
        ctx.should_call_api(
            "rest.actions.async_download_artifact",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "artifact_id": 123456789,
                    "archive_format": "zip",
                }
            ),
            mock_publish_download_artifact_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            snapshot({"owner": "he0119", "repo": "action-test", "issue_number": 101}),
            mock_remove_issue_resp,
        )
        ctx.receive_event(bot, event)
        ctx.should_pass_rule(pr_close_matcher)

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "config", "--global", "safe.directory", "*"],
            [
                "git",
                "config",
                "--global",
                "url.https://x-access-token:test-token@github.com/.insteadOf",
                "https://github.com/",
            ],
            ["git", "push", "origin", "--delete", "publish/issue76"],
            # 处理发布
            ["git", "checkout", "master"],
            ["git", "pull"],
            ["git", "switch", "-C", "publish/issue100"],
            ["git", "add", str(tmp_path / "bots.json5")],
            ["git", "config", "--global", "user.name", "test"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "test@users.noreply.github.com",
            ],
            ["git", "commit", "-m", ":beers: publish bot name (#100)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/publish/issue100", "publish/issue100"],
            ["git", "push", "origin", "publish/issue100", "-f"],
            # 处理移除
            ["git", "checkout", "master"],
            ["git", "pull"],
            ["git", "switch", "-C", "remove/issue101"],
            ["git", "add", str(tmp_path / "bots.json5")],
            ["git", "config", "--global", "user.name", "test"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "test@users.noreply.github.com",
            ],
            ["git", "commit", "-m", ":pencil2: remove CoolQBot (#101)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/remove/issue101", "remove/issue101"],
            ["git", "push", "origin", "remove/issue101", "-f"],
        ],
    )

    assert not mocked_api["homepage"].called
