import json
from pathlib import Path

import httpx
from githubkit import Response
from githubkit.exception import RequestFailed
from inline_snapshot import snapshot
from nonebot.adapters.github import IssueCommentCreated, IssuesOpened
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.plugins.github.event import get_mock_event
from tests.plugins.github.utils import (
    MockBody,
    MockIssue,
    assert_subprocess_run_calls,
    check_json_data,
    generate_issue_body_bot,
    get_github_bot,
    get_issue_labels,
    mock_subprocess_run_with_side_effect,
)


async def test_bot_process_publish_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试机器人的发布流程"""
    from src.plugins.github import plugin_config

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_issue = MockIssue(body=MockBody(type="bot", name="test").generate()).as_mock(
        mocker
    )

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = mock_pull

    with open(tmp_path / "bots.json5", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Bot: test

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_create",
            {
                "owner": "he0119",
                "repo": "action-test",
                "title": "Bot: test",
                "body": "resolve #80",
                "base": "master",
                "head": "publish/issue80",
            },
            mock_pulls_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_add_labels",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 2,
                "labels": ["Publish", "Bot"],
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "config", "--global", "safe.directory", "*"],
            ["git", "switch", "-C", "publish/issue80"],
            ["git", "ls-remote", "--heads", "origin", "publish/issue80"],
            ["git", "config", "--global", "user.name", "test"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "test@users.noreply.github.com",
            ],
            ["git", "add", "-A"],
            ["git", "commit", "-m", ":beers: publish bot test (#80)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/publish/issue80", "publish/issue80"],
            ["git", "push", "origin", "publish/issue80", "-f"],
        ],
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.bot_path,
        [
            {
                "name": "test",
                "desc": "desc",
                "author_id": 1,
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            }
        ],
    )

    assert mocked_api["homepage"].called


async def test_adapter_process_publish_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试适配器的发布流程"""
    from src.plugins.github import plugin_config

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_issue = MockIssue(
        body=MockBody(type="adapter", name="test").generate()
    ).as_mock(mocker)

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Adapter: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = mock_pull

    with open(tmp_path / "adapters.json5", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.adapter_path, [])

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        event.payload.issue.labels = get_issue_labels(["Adapter", "Publish"])

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Adapter: test

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 项目 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 标签: test-#ffffff。</li><li>✅ 版本号: 0.0.1。</li><li>✅ 发布时间：2023-09-01 08:00:00 CST。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 80,
                    "title": "Adapter: test",
                }
            ),
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_create",
            {
                "owner": "he0119",
                "repo": "action-test",
                "title": snapshot("Adapter: test"),
                "body": "resolve #80",
                "base": "master",
                "head": "publish/issue80",
            },
            mock_pulls_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_add_labels",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 2,
                "labels": ["Publish", "Adapter"],
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "config", "--global", "safe.directory", "*"],
            ["git", "switch", "-C", "publish/issue80"],
            ["git", "ls-remote", "--heads", "origin", "publish/issue80"],
            ["git", "config", "--global", "user.name", "test"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "test@users.noreply.github.com",
            ],
            ["git", "add", "-A"],
            ["git", "commit", "-m", ":beers: publish adapter test (#80)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/publish/issue80", "publish/issue80"],
            ["git", "push", "origin", "publish/issue80", "-f"],
        ],
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.adapter_path,
        [
            snapshot(
                {
                    "module_name": "module_name",
                    "project_link": "project_link",
                    "name": "test",
                    "desc": "desc",
                    "author_id": 1,
                    "homepage": "https://nonebot.dev",
                    "tags": [{"label": "test", "color": "#ffffff"}],
                    "is_official": False,
                }
            )
        ],
    )

    assert mocked_api["homepage"].called


async def test_plugin_process_publish_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试插件的发布流程"""
    from src.plugins.github import plugin_config
    from src.providers.docker_test import Metadata

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_issue = MockIssue(body=MockBody(type="plugin").generate()).as_mock(mocker)

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: name"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = mock_pull

    mock_test_result = mocker.MagicMock()
    mock_test_result.metadata = Metadata(
        name="name",
        desc="desc",
        homepage="https://nonebot.dev",
        type="application",
        supported_adapters=None,
    )
    mock_test_result.load = True
    mock_test_result.version = "1.0.0"
    mock_test_result.output = ""
    mock_docker = mocker.patch("src.providers.docker_test.DockerPluginTest.run")
    mock_docker.return_value = mock_test_result

    with open(tmp_path / "plugins.json5", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.plugin_path, [])

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        event.payload.issue.labels = get_issue_labels(["Plugin", "Publish"])

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 80,
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
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 80,
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
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Plugin: name

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 项目 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 标签: test-#ffffff。</li><li>✅ 插件类型: application。</li><li>✅ 插件支持的适配器: 所有。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li><li>✅ 版本号: 1.0.0。</li><li>✅ 发布时间：2023-09-01 08:00:00 CST。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 80,
                    "title": "Plugin: name",
                }
            ),
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_create",
            {
                "owner": "he0119",
                "repo": "action-test",
                "title": snapshot("Plugin: name"),
                "body": "resolve #80",
                "base": "master",
                "head": "publish/issue80",
            },
            mock_pulls_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_add_labels",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 2,
                "labels": ["Publish", "Plugin"],
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "config", "--global", "safe.directory", "*"],
            ["git", "switch", "-C", "publish/issue80"],
            ["git", "ls-remote", "--heads", "origin", "publish/issue80"],
            ["git", "config", "--global", "user.name", "test"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "test@users.noreply.github.com",
            ],
            ["git", "add", "-A"],
            ["git", "commit", "-m", ":beers: publish plugin name (#80)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/publish/issue80", "publish/issue80"],
            ["git", "push", "origin", "publish/issue80", "-f"],
        ],
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.plugin_path,
        [
            snapshot(
                {
                    "module_name": "module_name",
                    "project_link": "project_link",
                    "author_id": 1,
                    "tags": [{"label": "test", "color": "#ffffff"}],
                    "is_official": False,
                }
            )
        ],
    )

    assert mocked_api["homepage"].called
    mock_docker.assert_called_once_with("3.12")


async def test_plugin_process_publish_check_re_run(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试插件的发布流程，重新运行插件测试"""
    from src.plugins.github import plugin_config
    from src.providers.docker_test import Metadata

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    # 这次运行时，议题内容已经包含了插件测试按钮
    mock_issue = MockIssue(
        body=MockBody(type="plugin", test_button=True).generate()
    ).as_mock(mocker)

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: name"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = mock_pull

    mock_test_result = mocker.MagicMock()
    mock_test_result.metadata = Metadata(
        name="name",
        desc="desc",
        homepage="https://nonebot.dev",
        type="application",
        supported_adapters=None,
    )
    mock_test_result.load = True
    mock_test_result.version = "1.0.0"
    mock_test_result.output = ""
    mock_docker = mocker.patch("src.providers.docker_test.DockerPluginTest.run")
    mock_docker.return_value = mock_test_result

    with open(tmp_path / "plugins.json5", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.plugin_path, [])

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        event.payload.issue.labels = get_issue_labels(["Plugin", "Publish"])

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        # 测试前，将插件测试状态修改为插件测试中，提示用户
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 80,
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
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 80,
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
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Plugin: name

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 项目 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 标签: test-#ffffff。</li><li>✅ 插件类型: application。</li><li>✅ 插件支持的适配器: 所有。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li><li>✅ 版本号: 1.0.0。</li><li>✅ 发布时间：2023-09-01 08:00:00 CST。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 80,
                    "title": "Plugin: name",
                }
            ),
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_create",
            {
                "owner": "he0119",
                "repo": "action-test",
                "title": snapshot("Plugin: name"),
                "body": "resolve #80",
                "base": "master",
                "head": "publish/issue80",
            },
            mock_pulls_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_add_labels",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 2,
                "labels": ["Publish", "Plugin"],
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "config", "--global", "safe.directory", "*"],
            ["git", "switch", "-C", "publish/issue80"],
            ["git", "ls-remote", "--heads", "origin", "publish/issue80"],
            ["git", "config", "--global", "user.name", "test"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "test@users.noreply.github.com",
            ],
            ["git", "add", "-A"],
            ["git", "commit", "-m", ":beers: publish plugin name (#80)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/publish/issue80", "publish/issue80"],
            ["git", "push", "origin", "publish/issue80", "-f"],
        ],
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.plugin_path,
        [
            snapshot(
                {
                    "module_name": "module_name",
                    "project_link": "project_link",
                    "author_id": 1,
                    "tags": [{"label": "test", "color": "#ffffff"}],
                    "is_official": False,
                }
            )
        ],
    )

    assert mocked_api["homepage"].called
    mock_docker.assert_called_once_with("3.12")


async def test_edit_title(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试编辑标题

    名称被修改后，标题也应该被修改
    """
    from src.plugins.github import plugin_config

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_issue = MockIssue(body=MockBody(type="bot", name="test1").generate()).as_mock(
        mocker
    )

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pull.draft = False
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    with open(tmp_path / "bots.json5", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Bot: test1

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )
        # 修改议题标题
        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "title": "Bot: test1",
            },
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_create",
            {
                "owner": "he0119",
                "repo": "action-test",
                "title": "Bot: test1",
                "body": "resolve #80",
                "base": "master",
                "head": "publish/issue80",
            },
            exception=RequestFailed(
                Response(
                    httpx.Response(422, request=httpx.Request("test", "test")),
                    None,  # type: ignore
                )
            ),
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "he0119",
                "repo": "action-test",
                "head": "he0119:publish/issue80",
            },
            mock_pulls_resp,
        )
        # 修改拉取请求标题
        ctx.should_call_api(
            "rest.pulls.async_update",
            {
                "owner": "he0119",
                "repo": "action-test",
                "pull_number": 2,
                "title": "Bot: test1",
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "config", "--global", "safe.directory", "*"],
            ["git", "switch", "-C", "publish/issue80"],
            ["git", "ls-remote", "--heads", "origin", "publish/issue80"],
            ["git", "config", "--global", "user.name", "test"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "test@users.noreply.github.com",
            ],
            ["git", "add", "-A"],
            ["git", "commit", "-m", ":beers: publish bot test1 (#80)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/publish/issue80", "publish/issue80"],
            ["git", "push", "origin", "publish/issue80", "-f"],
        ],
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.bot_path,
        [
            {
                "name": "test1",
                "desc": "desc",
                "author_id": 1,
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            }
        ],
    )

    assert mocked_api["homepage"].called


async def test_edit_title_too_long(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试编辑标题

    标题过长的情况
    """
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(
        body=generate_issue_body_bot(
            name="looooooooooooooooooooooooooooooooooooooooooooooooooooooong"
        )
    ).as_mock(mocker)

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    with open(tmp_path / "bots.json5", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Bot: looooooooooooooooooooooooooooooooooooooooooooooooooooooong

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 名称: 字符过多。<dt>请确保其不超过 50 个字符。</dt></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )
        # 修改标题，应该被截断，且不会更新拉取请求的标题
        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "title": "Bot: looooooooooooooooooooooooooooooooooooooooooooooooo",
            },
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "he0119",
                "repo": "action-test",
                "head": "he0119:publish/issue80",
            },
            mock_pulls_resp,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            )  # type: ignore
        ]
    )

    # 检查文件是否正确
    check_json_data(plugin_config.input_config.bot_path, [])

    assert mocked_api["homepage"].called


async def test_process_publish_check_not_pass(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试发布检查不通过"""
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(
        body=generate_issue_body_bot(name="test", homepage="https://www.baidu.com")
    ).as_mock(mocker)

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    with open(tmp_path / "bots.json5", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        # 检查是否可以复用评论
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )

        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Bot: test

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保你的项目主页可访问。</dt></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "he0119",
                "repo": "action-test",
                "head": "he0119:publish/issue80",
            },
            mock_pulls_resp,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),  # type: ignore
        ]
    )

    # 检查文件是否正确
    check_json_data(plugin_config.input_config.bot_path, [])

    assert mocked_api["homepage_failed"].called


async def test_comment_at_pull_request(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试在拉取请求下评论

    event.issue.pull_request 不为空
    """
    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssueCommentCreated, "pr-comment")

        ctx.receive_event(bot, event)

    assert mocked_api.calls == []
    mock_subprocess_run.assert_not_called()


async def test_issue_state_closed(
    app: App, mocker: MockerFixture, mocked_api: MockRouter, mock_installation
) -> None:
    """测试议题已关闭

    event.issue.state = "closed"
    """
    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(state="closed").as_mock(mocker)
    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )

        ctx.receive_event(bot, event)

    assert mocked_api.calls == []
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),  # type: ignore
        ]
    )


async def test_not_publish_issue(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试议题与发布无关

    议题的标签不是 "Bot/Adapter/Plugin"
    """
    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        event.payload.issue.labels = []

        ctx.receive_event(bot, event)

    mock_subprocess_run.assert_not_called()


async def test_comment_by_self(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试自己评论触发的情况"""
    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssueCommentCreated, "issue-comment-bot")

        ctx.receive_event(bot, event)

    mock_subprocess_run.assert_not_called()


async def test_skip_plugin_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试手动跳过插件测试的流程"""
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(number=70, body=MockBody("plugin").generate()).as_mock(
        mocker
    )

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "/skip"
    mock_comment.author_association = "OWNER"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    with open(tmp_path / "plugins.json5", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.plugin_path, [])

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssueCommentCreated, "issue-comment-skip")

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 70},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 70,
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
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 70},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 70,
                    "body": """\
### 插件名称

### 插件描述

### 插件项目仓库/主页链接

### 插件类型

### 插件支持的适配器

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
        ctx.should_call_api(
            "rest.issues.async_update",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 70,
                "body": snapshot(
                    """\
### 插件名称

### 插件描述

### 插件项目仓库/主页链接

### 插件类型

### 插件支持的适配器

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
"""
                ),
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 70},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 70,
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Plugin: project_link

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 名称: 无法匹配到数据。<dt>请确保填写该数据项。</dt></li><li>⚠️ 描述: 无法匹配到数据。<dt>请确保填写该数据项。</dt></li><li>⚠️ 项目仓库/主页链接: 无法匹配到数据。<dt>请确保填写该数据项。</dt></li><li>⚠️ 插件类型: 无法匹配到数据。<dt>请确保填写该数据项。</dt></li><li>⚠️ 插件支持的适配器: 无法匹配到数据。<dt>请确保填写该数据项。</dt></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 标签: test-#ffffff。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 已跳过。</li><li>✅ 版本号: 0.0.1。</li><li>✅ 发布时间：2023-09-01 08:00:00 CST。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )
        ctx.should_call_api(
            "rest.issues.async_update",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 70,
                    "title": "Plugin: project_link",
                }
            ),
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "he0119",
                "repo": "action-test",
                "head": "he0119:publish/issue70",
            },
            mock_pulls_resp,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),  # type: ignore
        ]
    )

    # 检查文件是否正确
    check_json_data(plugin_config.input_config.plugin_path, [])

    assert mocked_api["pypi_project_link"].called


async def test_convert_pull_request_to_draft(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """未通过时将拉取请求转换为草稿"""
    from src.plugins.github import plugin_config

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

    mock_issue = MockIssue(
        number=80,
        body=generate_issue_body_bot(name="test", homepage="https://www.baidu.com"),
    ).as_mock(mocker)

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pull.title = "Bot: test"
    mock_pull.draft = False
    mock_pull.node_id = "123"
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    with open(tmp_path / "bots.json5", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        # 检查是否可以复用评论
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Bot: test

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保你的项目主页可访问。</dt></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "he0119",
                "repo": "action-test",
                "head": "he0119:publish/issue80",
            },
            mock_pulls_resp,
        )
        # 将拉取请求转换为草稿
        ctx.should_call_api(
            "async_graphql",
            {
                "query": "mutation convertPullRequestToDraft($pullRequestId: ID!) {\n                    convertPullRequestToDraft(input: {pullRequestId: $pullRequestId}) {\n                        clientMutationId\n                    }\n                }",
                "variables": {"pullRequestId": "123"},
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),  # type: ignore
        ]
    )

    # 检查文件是否正确
    check_json_data(plugin_config.input_config.bot_path, [])

    assert mocked_api["homepage_failed"].called


async def test_process_publish_check_ready_for_review(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """当之前失败后再次通过测试时，应该将拉取请求标记为 ready for review"""
    from src.plugins.github import plugin_config

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_issue = MockIssue(body=MockBody(type="bot", name="test").generate()).as_mock(
        mocker
    )

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.number = 2
    mock_pull.title = "Bot: test"
    mock_pull.draft = True
    mock_pull.node_id = "123"
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    with open(tmp_path / "bots.json5", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Bot: test

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_create",
            {
                "owner": "he0119",
                "repo": "action-test",
                "title": "Bot: test",
                "body": "resolve #80",
                "base": "master",
                "head": "publish/issue80",
            },
            exception=RequestFailed(
                Response(
                    httpx.Response(422, request=httpx.Request("test", "test")),
                    None,  # type: ignore
                )
            ),
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "he0119",
                "repo": "action-test",
                "head": "he0119:publish/issue80",
            },
            mock_pulls_resp,
        )
        # 将拉取请求标记为可供审阅
        ctx.should_call_api(
            "async_graphql",
            {
                "query": snapshot(
                    """\
mutation markPullRequestReadyForReview($pullRequestId: ID!) {
                        markPullRequestReadyForReview(input: {pullRequestId: $pullRequestId}) {
                            clientMutationId
                        }
                    }\
"""
                ),
                "variables": {"pullRequestId": "123"},
            },
            True,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "config", "--global", "safe.directory", "*"],
            ["git", "switch", "-C", "publish/issue80"],
            ["git", "ls-remote", "--heads", "origin", "publish/issue80"],
            ["git", "config", "--global", "user.name", "test"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "test@users.noreply.github.com",
            ],
            ["git", "add", "-A"],
            ["git", "commit", "-m", ":beers: publish bot test (#80)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/publish/issue80", "publish/issue80"],
            ["git", "push", "origin", "publish/issue80", "-f"],
        ],
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.bot_path,
        [
            {
                "name": "test",
                "desc": "desc",
                "author_id": 1,
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            }
        ],
    )

    assert mocked_api["homepage"].called


async def test_comment_immediate_after_pull_request_closed(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试在拉取请求关闭后立即评论

    此时分支还没有被删除，不应该再次创建拉取请求
    """
    from src.plugins.github import plugin_config

    mock_subprocess_run = mock_subprocess_run_with_side_effect(
        mocker,
        {"git ls-remote --heads origin publish/issue80": "refs/heads/publish/issue80"},
    )

    mock_issue = MockIssue(body=MockBody(type="bot", name="test").generate()).as_mock(
        mocker
    )

    mock_event = mocker.MagicMock()
    mock_event.issue = mock_issue

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Bot: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_pull = mocker.MagicMock()
    mock_pull.state = "closed"
    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    with open(tmp_path / "bots.json5", "w") as f:
        json.dump([], f)

    check_json_data(plugin_config.input_config.bot_path, [])

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)

        ctx.should_call_api(
            "rest.apps.async_get_repo_installation",
            {"owner": "he0119", "repo": "action-test"},
            mock_installation,
        )
        ctx.should_call_api(
            "rest.issues.async_get",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_issues_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "he0119", "repo": "action-test", "issue_number": 80},
            mock_list_comments_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_create_comment",
            {
                "owner": "he0119",
                "repo": "action-test",
                "issue_number": 80,
                "body": snapshot(
                    """\
# 📃 商店发布检查结果

> Bot: test

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 标签: test-#ffffff。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
                ),
            },
            True,
        )
        ctx.should_call_api(
            "rest.pulls.async_list",
            {
                "owner": "he0119",
                "repo": "action-test",
                "head": "he0119:publish/issue80",
            },
            mock_pulls_resp,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "config", "--global", "safe.directory", "*"],
            ["git", "switch", "-C", "publish/issue80"],
            ["git", "ls-remote", "--heads", "origin", "publish/issue80"],
            ["git", "config", "--global", "user.name", "test"],
            [
                "git",
                "config",
                "--global",
                "user.email",
                "test@users.noreply.github.com",
            ],
            ["git", "add", "-A"],
            ["git", "commit", "-m", ":beers: publish bot test (#80)"],
            ["git", "fetch", "origin"],
            ["git", "diff", "origin/publish/issue80", "publish/issue80"],
            ["git", "push", "origin", "publish/issue80", "-f"],
        ],
    )

    # 检查文件是否正确
    check_json_data(
        plugin_config.input_config.bot_path,
        [
            {
                "name": "test",
                "desc": "desc",
                "author_id": 1,
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            }
        ],
    )

    assert mocked_api["homepage"].called
