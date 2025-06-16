import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.plugins.github.utils import (
    GitHubApi,
    MockBody,
    MockIssue,
    MockUser,
    assert_subprocess_run_calls,
    check_json_data,
    get_github_bot,
    mock_subprocess_run_with_side_effect,
    should_call_apis,
)


@pytest.fixture
def mock_pull(mocker: MockerFixture):
    mock_pull = mocker.MagicMock()
    mock_pull.head.ref = "publish/issue1"
    mock_pull.draft = False

    return mock_pull


async def test_resolve_conflict_pull_requests_adapter(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path, mock_pull
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.handlers import GithubHandler
    from src.plugins.github.plugins.publish.utils import resolve_conflict_pull_requests
    from src.providers.models import (
        REGISTRY_DATA_NAME,
        AdapterPublishInfo,
        Color,
        RegistryArtifactData,
        RepoInfo,
        Tag,
    )
    from src.providers.utils import dump_json5

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_label = mocker.MagicMock()
    mock_label.name = "Adapter"

    mock_issue_resp = mocker.MagicMock()
    mock_issue = MockIssue(
        number=1,
        body=MockBody(type="adapter").generate(),
        user=MockUser(login="he0119", id=1),
    ).as_mock(mocker)
    mock_issue_resp.parsed_data = mock_issue

    mock_pull.title = "Adapter: OneBot V11"
    mock_pull.labels = [mock_label]

    mock_comment = mocker.MagicMock()
    mock_comment.body = """
<details>
<summary>历史测试</summary>
<pre><code>
<li>⚠️ <a href="https://github.com/owner/repo/actions/runs/14156878699">2025-03-28 02:21:18 CST</a></li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:21:18 CST</a></li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:22:18 CST</a>。</li><li>⚠️ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:22:18 CST</a></li>
</code></pre>
</details>
<!-- NONEFLOW -->
"""
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_artifact = mocker.MagicMock()
    mock_artifact.name = "noneflow"
    mock_artifact.id = 123456789
    mock_artifacts = mocker.MagicMock()
    mock_artifacts.artifacts = [mock_artifact]
    mock_artifact_resp = mocker.MagicMock()
    mock_artifact_resp.parsed_data = mock_artifacts

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
    info = AdapterPublishInfo.model_construct(**raw_data)
    registry_data = RegistryArtifactData.from_info(info)

    # 创建 zip 文件内容
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 将 registry_data 转换为 JSON 字符串并添加到 zip 中
        json_content = registry_data.model_dump_json(indent=2)
        zip_file.writestr(REGISTRY_DATA_NAME, json_content)

    # 获取 zip 文件的字节内容
    zip_content = zip_buffer.getvalue()

    mock_download_artifact_resp = mocker.MagicMock()
    mock_download_artifact_resp.content = zip_content

    dump_json5(
        tmp_path / "adapters.json5",
        [
            {
                "module_name": "nonebot.adapters.onebot.v11",
                "project_link": "nonebot-adapter-onebot",
                "name": "OneBot V11",
                "desc": "OneBot V11 协议",
                "author_id": 1,
                "homepage": "https://onebot.adapters.nonebot.dev/",
                "tags": [],
                "is_official": True,
            }
        ],
    )

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_get",
                    result=mock_issue_resp,
                ),
                GitHubApi(
                    api="rest.issues.async_list_comments",
                    result=mock_list_comments_resp,
                ),
                GitHubApi(
                    api="rest.actions.async_list_workflow_run_artifacts",
                    result=mock_artifact_resp,
                ),
                GitHubApi(
                    api="rest.actions.async_download_artifact",
                    result=mock_download_artifact_resp,
                ),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "issue_number": 1},
                    1: {"owner": "owner", "repo": "repo", "issue_number": 1},
                    2: {"owner": "owner", "repo": "repo", "run_id": 14156878699},
                    3: {
                        "owner": "owner",
                        "repo": "repo",
                        "artifact_id": 123456789,
                        "archive_format": "zip",
                    },
                }
            ),
        )

        await resolve_conflict_pull_requests(handler, [mock_pull])

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "checkout", "master"],
            ["git", "pull"],
            ["git", "switch", "-C", "publish/issue1"],
            ["git", "add", str(tmp_path / "adapters.json5")],
            ["git", "config", "--global", "user.name", "he0119"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "he0119@users.noreply.github.com",
            ],
            ["git", "commit", "-m", ":beers: publish adapter name (#1)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/publish/issue1", "publish/issue1"],
            ["git", "push", "origin", "publish/issue1", "-f"],
        ],
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.adapter_path,
        snapshot(
            [
                {
                    "module_name": "nonebot.adapters.onebot.v11",
                    "project_link": "nonebot-adapter-onebot",
                    "name": "OneBot V11",
                    "desc": "OneBot V11 协议",
                    "author_id": 1,
                    "homepage": "https://onebot.adapters.nonebot.dev/",
                    "tags": [],
                    "is_official": True,
                },
                {
                    "module_name": "module_name",
                    "project_link": "project_link",
                    "name": "name",
                    "desc": "desc",
                    "author_id": 1,
                    "homepage": "https://nonebot.dev",
                    "tags": [{"label": "test", "color": "#ffffff"}],
                    "is_official": False,
                },
            ]
        ),
    )

    assert not mocked_api["homepage"].called


async def test_resolve_conflict_pull_requests_bot(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path, mock_pull
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.handlers import GithubHandler
    from src.plugins.github.plugins.publish.utils import resolve_conflict_pull_requests
    from src.providers.models import (
        REGISTRY_DATA_NAME,
        BotPublishInfo,
        Color,
        RegistryArtifactData,
        RepoInfo,
        Tag,
    )
    from src.providers.utils import dump_json5

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_issue_repo = mocker.MagicMock()
    mock_issue = MockIssue(
        number=1,
        body=MockBody(type="bot").generate(),
        user=MockUser(login="he0119", id=1),
    ).as_mock(mocker)
    mock_issue_repo.parsed_data = mock_issue

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"

    mock_pull.labels = [mock_label]

    mock_comment = mocker.MagicMock()
    mock_comment.body = """
<details>
<summary>历史测试</summary>
<pre><code>
<li>⚠️ <a href="https://github.com/owner/repo/actions/runs/14156878699">2025-03-28 02:21:18 CST</a></li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:21:18 CST</a></li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:22:18 CST</a>。</li><li>⚠️ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:22:18 CST</a></li>
</code></pre>
</details>
<!-- NONEFLOW -->
"""
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_artifact = mocker.MagicMock()
    mock_artifact.name = "noneflow"
    mock_artifact.id = 123456789
    mock_artifacts = mocker.MagicMock()
    mock_artifacts.artifacts = [mock_artifact]
    mock_artifact_resp = mocker.MagicMock()
    mock_artifact_resp.parsed_data = mock_artifacts

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
    zip_content = zip_buffer.getvalue()

    mock_download_artifact_resp = mocker.MagicMock()
    mock_download_artifact_resp.content = zip_content

    dump_json5(
        tmp_path / "bots.json5",
        [
            {
                "name": "CoolQBot",
                "desc": "基于 NoneBot2 的聊天机器人",
                "author_id": 1,
                "homepage": "https://github.com/he0119/CoolQBot",
                "tags": [],
                "is_official": False,
            }
        ],
    )

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_get",
                    result=mock_issue_repo,
                ),
                GitHubApi(
                    api="rest.issues.async_list_comments",
                    result=mock_list_comments_resp,
                ),
                GitHubApi(
                    api="rest.actions.async_list_workflow_run_artifacts",
                    result=mock_artifact_resp,
                ),
                GitHubApi(
                    api="rest.actions.async_download_artifact",
                    result=mock_download_artifact_resp,
                ),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "issue_number": 1},
                    1: {"owner": "owner", "repo": "repo", "issue_number": 1},
                    2: {"owner": "owner", "repo": "repo", "run_id": 14156878699},
                    3: {
                        "owner": "owner",
                        "repo": "repo",
                        "artifact_id": 123456789,
                        "archive_format": "zip",
                    },
                }
            ),
        )

        await resolve_conflict_pull_requests(handler, [mock_pull])

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "checkout", "master"],
            ["git", "pull"],
            ["git", "switch", "-C", "publish/issue1"],
            ["git", "add", str(tmp_path / "bots.json5")],
            ["git", "config", "--global", "user.name", "he0119"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "he0119@users.noreply.github.com",
            ],
            ["git", "commit", "-m", ":beers: publish bot name (#1)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/publish/issue1", "publish/issue1"],
            ["git", "push", "origin", "publish/issue1", "-f"],
        ],
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.bot_path,
        snapshot(
            [
                {
                    "name": "CoolQBot",
                    "desc": "基于 NoneBot2 的聊天机器人",
                    "author_id": 1,
                    "homepage": "https://github.com/he0119/CoolQBot",
                    "tags": [],
                    "is_official": False,
                },
                {
                    "name": "name",
                    "desc": "desc",
                    "author_id": 1,
                    "homepage": "https://nonebot.dev",
                    "tags": [{"label": "test", "color": "#ffffff"}],
                    "is_official": False,
                },
            ]
        ),
    )

    assert not mocked_api["homepage"].called


async def test_resolve_conflict_pull_requests_plugin(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path, mock_pull
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.handlers import GithubHandler
    from src.plugins.github.plugins.publish.utils import resolve_conflict_pull_requests
    from src.providers.models import (
        REGISTRY_DATA_NAME,
        Color,
        PluginPublishInfo,
        RegistryArtifactData,
        RepoInfo,
        Tag,
    )
    from src.providers.utils import dump_json5

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_label = mocker.MagicMock()
    mock_label.name = "Plugin"

    mock_issue_repo = mocker.MagicMock()
    mock_issue = MockIssue(
        number=1,
        body=MockBody(type="plugin").generate(),
        user=MockUser(login="he0119", id=1),
    ).as_mock(mocker)
    mock_issue_repo.parsed_data = mock_issue

    mock_pull.labels = [mock_label]
    mock_pull.title = "Plugin: 帮助"

    mock_comment = mocker.MagicMock()
    mock_comment.body = """
<details>
<summary>历史测试</summary>
<pre><code>
<li>⚠️ <a href="https://github.com/owner/repo/actions/runs/14156878699">2025-03-28 02:21:18 CST</a></li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:21:18 CST</a></li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:22:18 CST</a>。</li><li>⚠️ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:22:18 CST</a></li>
</code></pre>
</details>
<!-- NONEFLOW -->
"""
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_artifact = mocker.MagicMock()
    mock_artifact.name = "noneflow"
    mock_artifact.id = 123456789
    mock_artifacts = mocker.MagicMock()
    mock_artifacts.artifacts = [mock_artifact]
    mock_artifact_resp = mocker.MagicMock()
    mock_artifact_resp.parsed_data = mock_artifacts

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
        "type": "application",
        "supported_adapters": None,
        "load": True,
        "skip_test": False,
        "test_output": "test_output",
        "test_result": None,
    }
    info = PluginPublishInfo.model_construct(**raw_data)
    registry_data = RegistryArtifactData.from_info(info)

    # 创建 zip 文件内容
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 将 registry_data 转换为 JSON 字符串并添加到 zip 中
        json_content = registry_data.model_dump_json(indent=2)
        zip_file.writestr(REGISTRY_DATA_NAME, json_content)

    # 获取 zip 文件的字节内容
    zip_content = zip_buffer.getvalue()

    mock_download_artifact_resp = mocker.MagicMock()
    mock_download_artifact_resp.content = zip_content

    dump_json5(
        tmp_path / "plugins.json5",
        [
            {
                "module_name": "nonebot_plugin_treehelp",
                "project_link": "nonebot-plugin-treehelp",
                "author_id": 1,
                "tags": [],
                "is_official": True,
            }
        ],
    )

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_get",
                    result=mock_issue_repo,
                ),
                GitHubApi(
                    api="rest.issues.async_list_comments",
                    result=mock_list_comments_resp,
                ),
                GitHubApi(
                    api="rest.actions.async_list_workflow_run_artifacts",
                    result=mock_artifact_resp,
                ),
                GitHubApi(
                    api="rest.actions.async_download_artifact",
                    result=mock_download_artifact_resp,
                ),
            ],
            snapshot(
                {
                    0: {"owner": "owner", "repo": "repo", "issue_number": 1},
                    1: {"owner": "owner", "repo": "repo", "issue_number": 1},
                    2: {"owner": "owner", "repo": "repo", "run_id": 14156878699},
                    3: {
                        "owner": "owner",
                        "repo": "repo",
                        "artifact_id": 123456789,
                        "archive_format": "zip",
                    },
                }
            ),
        )

        await resolve_conflict_pull_requests(handler, [mock_pull])

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "checkout", "master"],
            ["git", "pull"],
            ["git", "switch", "-C", "publish/issue1"],
            ["git", "add", str(tmp_path / "plugins.json5")],
            ["git", "config", "--global", "user.name", "he0119"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "he0119@users.noreply.github.com",
            ],
            ["git", "commit", "-m", ":beers: publish plugin name (#1)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/publish/issue1", "publish/issue1"],
            ["git", "push", "origin", "publish/issue1", "-f"],
        ],
    )

    # 检查文件是否正确
    # 因为没有进行 git 操作，所有会有两个插件信息
    check_json_data(
        plugin_config.input_config.plugin_path,
        snapshot(
            [
                {
                    "module_name": "nonebot_plugin_treehelp",
                    "project_link": "nonebot-plugin-treehelp",
                    "author_id": 1,
                    "tags": [],
                    "is_official": True,
                },
                {
                    "module_name": "module_name",
                    "project_link": "project_link",
                    "author_id": 1,
                    "tags": [{"label": "test", "color": "#ffffff"}],
                    "is_official": False,
                },
            ]
        ),
    )

    assert not mocked_api["homepage"].called


async def test_resolve_conflict_pull_requests_plugin_not_valid(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path, mock_pull
) -> None:
    """测试插件信息不合法的情况"""
    from src.plugins.github import plugin_config
    from src.plugins.github.handlers import GithubHandler
    from src.plugins.github.plugins.publish.utils import resolve_conflict_pull_requests
    from src.providers.models import RepoInfo
    from src.providers.utils import dump_json5

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_label = mocker.MagicMock()
    mock_label.name = "Plugin"

    mock_issue_repo = mocker.MagicMock()
    mock_issue = MockIssue(
        number=1,
        body=MockBody(type="plugin").generate(),
        user=MockUser(login="he0119", id=1),
    ).as_mock(mocker)
    mock_issue_repo.parsed_data = mock_issue

    mock_pull.labels = [mock_label]
    mock_pull.title = "Plugin: 帮助"

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    dump_json5(
        tmp_path / "plugins.json5",
        [
            {
                "module_name": "nonebot_plugin_treehelp",
                "project_link": "nonebot-plugin-treehelp",
                "author_id": 1,
                "tags": [],
                "is_official": True,
            }
        ],
    )

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_get",
                    result=mock_issue_repo,
                ),
                GitHubApi(
                    api="rest.issues.async_list_comments",
                    result=mock_list_comments_resp,
                ),
            ],
            [
                snapshot({"owner": "owner", "repo": "repo", "issue_number": 1}),
                {"owner": "owner", "repo": "repo", "issue_number": 1},
            ],
        )

        await resolve_conflict_pull_requests(handler, [mock_pull])

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()

    # 检查文件是否正确
    # 因为没有进行 git 操作，所有会有两个插件信息
    check_json_data(
        plugin_config.input_config.plugin_path,
        snapshot(
            [
                {
                    "module_name": "nonebot_plugin_treehelp",
                    "project_link": "nonebot-plugin-treehelp",
                    "author_id": 1,
                    "tags": [],
                    "is_official": True,
                },
            ]
        ),
    )

    assert not mocked_api["homepage"].called


async def test_resolve_conflict_pull_requests_draft(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.handlers import GithubHandler
    from src.plugins.github.plugins.publish.utils import resolve_conflict_pull_requests
    from src.providers.models import RepoInfo
    from src.providers.utils import dump_json5

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"

    mock_pull = mocker.MagicMock()
    mock_pull.head.ref = "publish/issue1"
    mock_pull.draft = True
    mock_pull.labels = [mock_label]

    dump_json5(
        tmp_path / "bots.json5",
        [
            {
                "name": "CoolQBot",
                "desc": "基于 NoneBot2 的聊天机器人",
                "author_id": 1,
                "homepage": "https://github.com/he0119/CoolQBot",
                "tags": [],
                "is_official": False,
            }
        ],
    )

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        await resolve_conflict_pull_requests(handler, [mock_pull])

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.bot_path,
        [
            {
                "name": "CoolQBot",
                "desc": "基于 NoneBot2 的聊天机器人",
                "author_id": 1,
                "homepage": "https://github.com/he0119/CoolQBot",
                "tags": [],
                "is_official": False,
            }
        ],
    )

    assert not mocked_api["homepage"].called


async def test_resolve_conflict_pull_requests_ref(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, tmp_path: Path
) -> None:
    from src.plugins.github import plugin_config
    from src.plugins.github.handlers import GithubHandler
    from src.plugins.github.plugins.publish.utils import resolve_conflict_pull_requests
    from src.providers.models import RepoInfo
    from src.providers.utils import dump_json5

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"

    mock_pull = mocker.MagicMock()
    mock_pull.head.ref = "publish/issue"
    mock_pull.draft = False
    mock_pull.labels = [mock_label]

    dump_json5(
        tmp_path / "bots.json5",
        [
            {
                "name": "CoolQBot",
                "desc": "基于 NoneBot2 的聊天机器人",
                "author_id": 1,
                "homepage": "https://github.com/he0119/CoolQBot",
                "tags": [],
                "is_official": False,
            }
        ],
    )

    async with app.test_api() as ctx:
        adapter, bot = get_github_bot(ctx)

        handler = GithubHandler(bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"))

        await resolve_conflict_pull_requests(handler, [mock_pull])

    # 测试 git 命令
    mock_subprocess_run.assert_not_called()

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.bot_path,
        [
            {
                "name": "CoolQBot",
                "desc": "基于 NoneBot2 的聊天机器人",
                "author_id": 1,
                "homepage": "https://github.com/he0119/CoolQBot",
                "tags": [],
                "is_official": False,
            }
        ],
    )

    assert not mocked_api["homepage"].called
