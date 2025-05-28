from githubkit.rest import Issue
from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.plugins.github.utils import (
    generate_issue_body_adapter,
    generate_issue_body_bot,
    generate_issue_body_plugin,
    generate_issue_body_plugin_skip_test,
    get_github_bot,
)


async def test_validate_info_from_issue_adapter(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    from src.plugins.github.plugins.publish.validation import (
        validate_adapter_info_from_issue,
    )

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_adapter()
    mock_issue.user.login = "test"

    result = await validate_adapter_info_from_issue(mock_issue)

    assert result.valid
    assert mocked_api["homepage"].called


async def test_validate_info_from_issue_bot(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    from src.plugins.github.plugins.publish.validation import (
        validate_bot_info_from_issue,
    )

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_bot()
    mock_issue.user.login = "test"

    result = await validate_bot_info_from_issue(mock_issue)

    assert result.valid
    assert mocked_api["homepage"].called


async def test_validate_info_from_issue_plugin(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    from src.plugins.github import plugin_config
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.validation import (
        validate_plugin_info_from_issue,
    )
    from src.providers.docker_test import Metadata
    from src.providers.models import RepoInfo

    mock_user = mocker.MagicMock()
    mock_user.login = "test"
    mock_user.id = 1

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.body = generate_issue_body_plugin()
    mock_issue.number = 1
    mock_issue.user = mock_user

    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = []

    mock_test_result = mocker.MagicMock()
    mock_test_result.metadata = Metadata(
        name="name",
        desc="desc",
        homepage="https://nonebot.dev",
        type="application",
        supported_adapters=["~onebot.v11"],
    )
    mock_test_result.version = "1.0.0"
    mock_test_result.load = True
    mock_test_result.output = 'require("nonebot_plugin_alconna")\ntest'
    mock_docker = mocker.patch("src.providers.docker_test.DockerPluginTest.run")
    mock_docker.return_value = mock_test_result

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)
        handler = IssueHandler(
            bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"), issue=mock_issue
        )

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "repo", "issue_number": 1},
            mock_list_comments_resp,
        )

        result = await validate_plugin_info_from_issue(handler)

    assert result.valid
    assert mocked_api["homepage"].called
    assert plugin_config.github_step_summary.read_text(encoding="utf-8") == snapshot(
        """\
# 📃 插件 project_link (1.0.0)

> **✅ 插件已尝试运行**
> **✅ 插件加载成功**

## 插件元数据

<pre><code>{
  &#34;name&#34;: &#34;name&#34;,
  &#34;desc&#34;: &#34;desc&#34;,
  &#34;homepage&#34;: &#34;https://nonebot.dev&#34;,
  &#34;type&#34;: &#34;application&#34;,
  &#34;supported_adapters&#34;: [
    &#34;~onebot.v11&#34;
  ]
}</code></pre>

## 插件输出

<pre><code>require(&#34;nonebot_plugin_alconna&#34;)
test</code></pre>

---

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
"""
    )


async def test_validate_info_from_issue_plugin_skip_test(
    app: App, mocker: MockerFixture, mocked_api: MockRouter
):
    """跳过插件测试的情况"""
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.validation import (
        validate_plugin_info_from_issue,
    )
    from src.providers.models import RepoInfo

    mock_user = mocker.MagicMock()
    mock_user.login = "test"
    mock_user.id = 1

    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.body = generate_issue_body_plugin_skip_test()
    mock_issue.number = 1
    mock_issue.user = mock_user

    mock_comment = mocker.MagicMock()
    mock_comment.body = "/skip"
    mock_comment.author_association = "MEMBER"
    mock_list_comments_resp = mocker.MagicMock()
    mock_list_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        _, bot = get_github_bot(ctx)
        handler = IssueHandler(
            bot=bot, repo_info=RepoInfo(owner="owner", repo="repo"), issue=mock_issue
        )

        ctx.should_call_api(
            "rest.issues.async_list_comments",
            {"owner": "owner", "repo": "repo", "issue_number": 1},
            mock_list_comments_resp,
        )

        result = await validate_plugin_info_from_issue(handler)

    assert result.valid
    assert mocked_api["homepage"].called
