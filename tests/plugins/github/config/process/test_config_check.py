import os
from pathlib import Path

from inline_snapshot import snapshot
from nonebot.adapters.github import IssuesOpened
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.plugins.github.config.utils import generate_issue_body
from tests.plugins.github.event import get_mock_event
from tests.plugins.github.utils import (
    GitHubApi,
    MockIssue,
    assert_subprocess_run_calls,
    check_json_data,
    get_github_bot,
    get_issue_labels,
    mock_subprocess_run_with_side_effect,
    should_call_apis,
)


def get_config_labels():
    return get_issue_labels(["Config", "Plugin"])


async def test_process_config_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
    mock_installation_token,
    mock_results: dict[str, Path],
) -> None:
    """测试发布检查不通过"""
    from src.providers.docker_test import Metadata

    # 更改当前工作目录为临时目录
    os.chdir(tmp_path)

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_issue = MockIssue(
        body=generate_issue_body(
            module_name="nonebot_plugin_treehelp",
            project_link="nonebot-plugin-treehelp",
        )
    ).as_mock(mocker)

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pull = mocker.MagicMock()
    mock_pull.number = 100
    mock_pull_resp = mocker.MagicMock()
    mock_pull_resp.parsed_data = mock_pull

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: test"

    mock_self_comment = mocker.MagicMock()
    mock_self_comment.id = 123
    mock_self_comment.body = """\
# 📃 商店发布检查结果

> Plugin: AI群聊机器人

[![主页](https://img.shields.io/badge/HOMEPAGE-200-green?style=for-the-badge)](https://github.com/KarisAya/nonebot_plugin_groups_aichat) [![测试结果](https://img.shields.io/badge/RESULT-OK-green?style=for-the-badge)](https://github.com/nonebot/registry/actions/runs/15942511177)

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://github.com/KarisAya/nonebot_plugin_groups_aichat">主页</a> 返回状态码 200。</li><li>✅ 项目 <a href="https://pypi.org/project/nonebot-plugin-groups-aichat/">nonebot-plugin-groups-aichat</a> 已发布至 PyPI。</li><li>✅ 标签: ChatGPT-#33cc99, Gemini-#59fb51, DeepSeek-#3399aa。</li><li>✅ 插件类型: application。</li><li>✅ 插件支持的适配器: 所有。</li><li>✅ 插件 <a href="https://github.com/nonebot/registry/actions/runs/15942511177">加载测试</a> 通过。</li><li>✅ 版本号: 0.2.0。</li><li>✅ 发布时间：2025-06-27 21:20:30 CST。</li></code></pre>
</details>
<details>
<summary>历史测试</summary>
<pre><code><li>✅ <a href="https://github.com/nonebot/registry/actions/runs/15942511177">2025-06-28 16:58:15 CST</a></li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment, mock_self_comment]

    mock_test_result = mocker.MagicMock()
    mock_test_result.metadata = Metadata(
        name="name",
        desc="desc",
        homepage="https://nonebot.dev",
        type="application",
        supported_adapters=["~onebot.v11"],
    )
    mock_test_result.load = True
    mock_test_result.version = "1.0.0"
    mock_test_result.output = ""
    mock_docker = mocker.patch("src.providers.docker_test.DockerPluginTest.run")
    mock_docker.return_value = mock_test_result

    async with app.test_matcher() as ctx:
        _adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        event.payload.issue.labels = get_config_labels()

        # 定义要调用的 API 列表
        apis: list[GitHubApi] = [
            {
                "api": "rest.apps.async_get_repo_installation",
                "result": mock_installation,
            },
            {
                "api": "rest.apps.async_create_installation_access_token",
                "result": mock_installation_token,
            },
            {
                "api": "rest.issues.async_get",
                "result": mock_issues_resp,
            },
            {
                "api": "rest.issues.async_update",
                "result": None,
            },
            {
                "api": "rest.issues.async_list_comments",
                "result": mock_list_comments_resp,
            },
            {
                "api": "rest.issues.async_update_comment",
                "result": True,
            },
            {
                "api": "rest.issues.async_update",
                "result": None,
            },
            {
                "api": "rest.pulls.async_create",
                "result": mock_pull_resp,
            },
            {
                "api": "rest.issues.async_add_labels",
                "result": None,
            },
            {
                "api": "rest.issues.async_update",
                "result": None,
            },
        ]

        # 对应的 API 数据
        api_data = [
            {"owner": "he0119", "repo": "action-test"},
            {"installation_id": mock_installation.parsed_data.id},
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 80,
                    "body": """\
### PyPI 项目名

nonebot-plugin-treehelp

### 插件模块名

nonebot_plugin_treehelp

### 插件配置项

```dotenv
log_level=DEBUG
```

### 插件测试

- [x] 🔥插件测试中，请稍候\
""",
                }
            ),
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "comment_id": 123,
                    "body": """\
# 📃 商店发布检查结果

> Plugin: name

[![主页](https://img.shields.io/badge/HOMEPAGE-200-green?style=for-the-badge)](https://nonebot.dev) [![测试结果](https://img.shields.io/badge/RESULT-OK-green?style=for-the-badge)](https://github.com/owner/repo/actions/runs/123456)

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 项目 <a href="https://pypi.org/project/nonebot-plugin-treehelp/">nonebot-plugin-treehelp</a> 已发布至 PyPI。</li><li>✅ 标签: test-#ffffff。</li><li>✅ 插件类型: application。</li><li>✅ 插件支持的适配器: nonebot.adapters.onebot.v11。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li><li>✅ 版本号: 1.0.0。</li><li>✅ 发布时间：2024-07-13 12:41:40 CST。</li></code></pre>
</details>
<details>
<summary>历史测试</summary>
<pre><code><li>✅ <a href="https://github.com/nonebot/registry/actions/runs/15942511177">2025-06-28 16:58:15 CST</a></li><li>✅ <a href="https://github.com/owner/repo/actions/runs/123456">2023-08-23 09:22:14 CST</a></li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
""",
                }
            ),
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 80,
                    "title": "Plugin: name",
                }
            ),
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "title": "Plugin: name",
                    "body": "resolve #80",
                    "base": "results",
                    "head": "config/issue80",
                }
            ),
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 100,
                    "labels": ["Plugin", "Config"],
                }
            ),
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 80,
                    "body": """\
### PyPI 项目名

nonebot-plugin-treehelp

### 插件模块名

nonebot_plugin_treehelp

### 插件配置项

```dotenv
log_level=DEBUG
```

### 插件测试

- [ ] 如需重新运行插件测试，请勾选左侧勾选框\
""",
                }
            ),
        ]

        # 使用辅助函数调用 API
        should_call_apis(ctx, apis, api_data)

        ctx.receive_event(bot, event)  # 测试 git 命令

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
            ["git", "fetch", "origin", "results"],
            ["git", "checkout", "results"],
            ["git", "switch", "-C", "config/issue80"],
            ["git", "add", "-A"],
            ["git", "config", "--global", "user.name", "test"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "test@users.noreply.github.com",
            ],
            ["git", "commit", "-m", "chore: edit config plugin name (#80)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/config/issue80", "config/issue80"],
            ["git", "push", "origin", "config/issue80", "-f"],
        ],
    )

    # 检查文件是否正确
    check_json_data(
        mock_results["plugins"],
        snapshot(
            [
                {
                    "module_name": "nonebot_plugin_treehelp",
                    "project_link": "nonebot-plugin-treehelp",
                    "name": "name",
                    "desc": "desc",
                    "author": "test",
                    "homepage": "https://nonebot.dev",
                    "tags": [{"label": "test", "color": "#ffffff"}],
                    "is_official": False,
                    "type": "application",
                    "supported_adapters": ["nonebot.adapters.onebot.v11"],
                    "valid": True,
                    "time": "2024-07-13T04:41:40.905441Z",
                    "version": "1.0.0",
                    "skip_test": False,
                }
            ]
        ),
    )
    check_json_data(
        mock_results["results"],
        snapshot(
            {
                "nonebot-plugin-treehelp:nonebot_plugin_treehelp": {
                    "time": "2023-08-23T09:22:14.836035+08:00",
                    "config": "log_level=DEBUG",
                    "version": "1.0.0",
                    "test_env": {"python==3.12": True},
                    "results": {"validation": True, "load": True, "metadata": True},
                    "outputs": {
                        "validation": None,
                        "load": "",
                        "metadata": {
                            "name": "name",
                            "description": "desc",
                            "homepage": "https://nonebot.dev",
                            "type": "application",
                            "supported_adapters": ["nonebot.adapters.onebot.v11"],
                        },
                    },
                }
            }
        ),
    )
    check_json_data(
        mock_results["plugin_configs"],
        snapshot(
            {"nonebot-plugin-treehelp:nonebot_plugin_treehelp": "log_level=DEBUG"}
        ),
    )

    assert mocked_api["homepage"].called
