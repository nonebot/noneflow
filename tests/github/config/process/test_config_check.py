import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from inline_snapshot import snapshot
from nonebot.adapters.github import IssuesOpened
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.github.config.utils import generate_issue_body
from tests.github.event import get_mock_event
from tests.github.utils import (
    MockIssue,
    check_json_data,
    get_github_bot,
    get_issue_labels,
)


def get_config_labels():
    return get_issue_labels(["Config", "Plugin"])


async def test_process_config_check(
    app: App,
    mocker: MockerFixture,
    mocked_api: MockRouter,
    tmp_path: Path,
    mock_installation,
    mock_results: dict[str, Path],
) -> None:
    """测试发布检查不通过"""
    from src.providers.docker_test import Metadata

    # 更改当前工作目录为临时目录
    os.chdir(tmp_path)

    mock_datetime = mocker.patch("src.providers.models.datetime")
    mock_datetime.now.return_value = datetime(
        2023, 8, 23, 9, 22, 14, 836035, tzinfo=ZoneInfo("Asia/Shanghai")
    )

    mock_subprocess_run = mocker.patch(
        "subprocess.run", side_effect=lambda *args, **kwargs: mocker.MagicMock()
    )

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
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

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
    mock_docker = mocker.patch("src.providers.docker_test.DockerPluginTest.run")
    mock_docker.return_value = mock_test_result

    async with app.test_matcher() as ctx:
        adapter, bot = get_github_bot(ctx)
        event = get_mock_event(IssuesOpened)
        event.payload.issue.labels = get_config_labels()

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

> Plugin: name

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://pypi.org/project/nonebot-plugin-treehelp/">nonebot-plugin-treehelp</a> 已发布至 PyPI。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 标签: test-#ffffff。</li><li>✅ 插件类型: application。</li><li>✅ 插件支持的适配器: nonebot.adapters.onebot.v11。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>
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
            mock_pull_resp,
        )
        ctx.should_call_api(
            "rest.issues.async_add_labels",
            snapshot(
                {
                    "owner": "he0119",
                    "repo": "action-test",
                    "issue_number": 100,
                    "labels": ["Plugin", "Config"],
                }
            ),
            None,
        )

        ctx.receive_event(bot, event)

    # 测试 git 命令
    mock_subprocess_run.assert_has_calls(
        [
            mocker.call(
                ["git", "config", "--global", "safe.directory", "*"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["pre-commit", "install", "--install-hooks"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "fetch", "origin", "results"], check=True, capture_output=True
            ),
            mocker.call(
                ["git", "checkout", "results"], check=True, capture_output=True
            ),
            mocker.call(
                ["git", "switch", "-C", "config/issue80"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "config", "--global", "user.name", "test"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                [
                    "git",
                    "config",
                    "--global",
                    "user.email",
                    "test@users.noreply.github.com",
                ],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "add", "-A"], check=True, capture_output=True),
            mocker.call(
                ["git", "commit", "-m", "chore: edit config plugin name (#80)"],
                check=True,
                capture_output=True,
            ),
            mocker.call(["git", "fetch", "origin"], check=True, capture_output=True),
            mocker.call(
                ["git", "diff", "origin/config/issue80", "config/issue80"],
                check=True,
                capture_output=True,
            ),
            mocker.call(
                ["git", "push", "origin", "config/issue80", "-f"],
                check=True,
                capture_output=True,
            ),
        ]  # type: ignore
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
                    "time": "2021-08-01T00:00:00+00:00",
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
                            "desc": "desc",
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
