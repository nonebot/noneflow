import json
from pathlib import Path

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
    generate_issue_body_plugin,
    get_github_bot,
    get_issue_labels,
    mock_subprocess_run_with_side_effect,
    should_call_apis,
)


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

        ctx.receive_event(bot, event)
        should_call_apis(
            ctx,
            [
                {
                    "api": "rest.apps.async_get_repo_installation",
                    "result": mock_installation,
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
                    "api": "rest.issues.async_update",
                    "result": None,
                },
                {
                    "api": "rest.issues.async_list_comments",
                    "result": mock_list_comments_resp,
                },
                {
                    "api": "rest.issues.async_create_comment",
                    "result": None,
                },
                {
                    "api": "rest.issues.async_update",
                    "result": None,
                },
                {
                    "api": "rest.pulls.async_create",
                    "result": mock_pulls_resp,
                },
                {
                    "api": "rest.issues.async_add_labels",
                    "result": None,
                },
            ],
            snapshot(
                {
                    0: {"owner": "he0119", "repo": "action-test"},
                    1: {"owner": "he0119", "repo": "action-test", "issue_number": 80},
                    2: {
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
                    },
                    3: {"owner": "he0119", "repo": "action-test", "issue_number": 80},
                    4: {
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
                    },
                    5: {"owner": "he0119", "repo": "action-test", "issue_number": 80},
                    6: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "issue_number": 80,
                        "body": """\
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
""",
                    },
                    7: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "issue_number": 80,
                        "title": "Plugin: name",
                    },
                    8: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "title": "Plugin: name",
                        "body": "resolve #80",
                        "base": "master",
                        "head": "publish/issue80",
                    },
                    9: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "issue_number": 2,
                        "labels": ["Publish", "Plugin"],
                    },
                }
            ),
        )

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
    ).as_mock()

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

        ctx.receive_event(bot, event)
        should_call_apis(
            ctx,
            [
                {
                    "api": "rest.apps.async_get_repo_installation",
                    "result": mock_installation,
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
                    "api": "rest.issues.async_update",
                    "result": None,
                },
                {
                    "api": "rest.issues.async_list_comments",
                    "result": mock_list_comments_resp,
                },
                {
                    "api": "rest.issues.async_create_comment",
                    "result": None,
                },
                {
                    "api": "rest.issues.async_update",
                    "result": None,
                },
                {
                    "api": "rest.pulls.async_create",
                    "result": mock_pulls_resp,
                },
                {
                    "api": "rest.issues.async_add_labels",
                    "result": None,
                },
            ],
            snapshot(
                {
                    0: {"owner": "he0119", "repo": "action-test"},
                    1: {"owner": "he0119", "repo": "action-test", "issue_number": 80},
                    2: {
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
                    },
                    3: {"owner": "he0119", "repo": "action-test", "issue_number": 80},
                    4: {
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
                    },
                    5: {"owner": "he0119", "repo": "action-test", "issue_number": 80},
                    6: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "issue_number": 80,
                        "body": """\
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
""",
                    },
                    7: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "issue_number": 80,
                        "title": "Plugin: name",
                    },
                    8: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "title": "Plugin: name",
                        "body": "resolve #80",
                        "base": "master",
                        "head": "publish/issue80",
                    },
                    9: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "issue_number": 2,
                        "labels": ["Publish", "Plugin"],
                    },
                }
            ),
        )

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


async def test_plugin_process_publish_check_missing_metadata(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试发布检查不通过，测试缺少插件元数据"""
    from src.plugins.github import plugin_config

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_issue = MockIssue(
        title="Plugin: test",
        body=generate_issue_body_plugin(),
    ).as_mock()

    mock_issues_resp = mocker.MagicMock()
    mock_issues_resp.parsed_data = mock_issue

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = []

    mock_comment = mocker.MagicMock()
    mock_comment.body = "Plugin: test"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    mock_test_result = mocker.MagicMock()
    mock_test_result.metadata = None
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

        ctx.receive_event(bot, event)
        should_call_apis(
            ctx,
            [
                {
                    "api": "rest.apps.async_get_repo_installation",
                    "result": mock_installation,
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
                    "api": "rest.issues.async_update",
                    "result": None,
                },
                {
                    "api": "rest.issues.async_list_comments",
                    "result": mock_list_comments_resp,
                },
                {
                    "api": "rest.issues.async_create_comment",
                    "result": None,
                },
                {
                    "api": "rest.issues.async_update",
                    "result": None,
                },
                {
                    "api": "rest.pulls.async_list",
                    "result": mock_pulls_resp,
                },
            ],
            snapshot(
                {
                    0: {"owner": "he0119", "repo": "action-test"},
                    1: {"owner": "he0119", "repo": "action-test", "issue_number": 80},
                    2: {
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
                    },
                    3: {"owner": "he0119", "repo": "action-test", "issue_number": 80},
                    4: {
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
                    },
                    5: {"owner": "he0119", "repo": "action-test", "issue_number": 80},
                    6: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "issue_number": 80,
                        "body": """\
# 📃 商店发布检查结果

> Plugin: project_link

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 无法获取到插件元数据。<dt>请确保插件正常加载。</dt></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 标签: test-#ffffff。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li><li>✅ 版本号: 1.0.0。</li><li>✅ 发布时间：2023-09-01 08:00:00 CST。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
""",
                    },
                    7: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "issue_number": 80,
                        "title": "Plugin: project_link",
                    },
                    8: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "head": "he0119:publish/issue80",
                    },
                }
            ),
        )

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "config", "--global", "safe.directory", "*"],
        ],
    )

    # 检查文件是否正确
    check_json_data(plugin_config.input_config.plugin_path, [])

    assert not mocked_api["homepage"].called


async def test_skip_plugin_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
) -> None:
    """测试手动跳过插件测试的流程"""
    from src.plugins.github import plugin_config

    mock_subprocess_run = mock_subprocess_run_with_side_effect(mocker)

    mock_issue = MockIssue(number=70, body=MockBody("plugin").generate()).as_mock()

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

        ctx.receive_event(bot, event)
        should_call_apis(
            ctx,
            [
                # 获取安装信息
                {
                    "api": "rest.apps.async_get_repo_installation",
                    "result": mock_installation,
                },
                # 获取议题信息
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
                    "api": "rest.issues.async_update",
                    "result": None,
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
                    "api": "rest.issues.async_create_comment",
                    "result": None,
                },
                {
                    "api": "rest.issues.async_update",
                    "result": None,
                },
                {
                    "api": "rest.pulls.async_list",
                    "result": mock_pulls_resp,
                },
            ],
            snapshot(
                {
                    0: {"owner": "he0119", "repo": "action-test"},
                    1: {"owner": "he0119", "repo": "action-test", "issue_number": 70},
                    2: {
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
                    },
                    3: {"owner": "he0119", "repo": "action-test", "issue_number": 70},
                    4: {
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
                    },
                    5: {
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

- [ ] 如需重新运行插件测试，请勾选左侧勾选框\
""",
                    },
                    6: {"owner": "he0119", "repo": "action-test", "issue_number": 70},
                    7: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "issue_number": 70,
                        "body": """\
# 📃 商店发布检查结果

> Plugin: project_link

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 名称: 无法匹配到数据。<dt>请确保填写该数据项。</dt></li><li>⚠️ 描述: 无法匹配到数据。<dt>请确保填写该数据项。</dt></li><li>⚠️ 项目仓库/主页链接: 无法匹配到数据。<dt>请确保填写该数据项。</dt></li><li>⚠️ 插件类型: 无法匹配到数据。<dt>请确保填写该数据项。</dt></li><li>⚠️ 插件支持的适配器: 无法匹配到数据。<dt>请确保填写该数据项。</dt></li><li>⚠️ 无法获取到插件元数据。<dt>请确保插件正常加载。</dt></li></code></pre>

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
""",
                    },
                    8: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "issue_number": 70,
                        "title": "Plugin: project_link",
                    },
                    9: {
                        "owner": "he0119",
                        "repo": "action-test",
                        "head": "he0119:publish/issue70",
                    },
                }
            ),
        )

    # 测试 git 命令
    assert_subprocess_run_calls(
        mock_subprocess_run,
        [
            ["git", "config", "--global", "safe.directory", "*"],
        ],
    )

    # 检查文件是否正确
    check_json_data(plugin_config.input_config.plugin_path, [])

    assert mocked_api["pypi_project_link"].called
