import pytest
from githubkit.rest import Issue
from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockerFixture

from tests.plugins.github.utils import GitHubApi, get_github_bot, should_call_apis


async def test_get_noneflow_artifact_success(app: App, mocker: MockerFixture) -> None:
    """测试成功获取 noneflow artifact"""
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.utils import get_noneflow_artifact
    from src.providers.models import RepoInfo

    # 模拟评论内容，包含历史工作流信息
    comment_body = """
# 📃 商店发布检查结果

<details>
<summary>历史测试</summary>
<pre><code>
<li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/12345678901">2025-03-28 02:22:18 CST</a></li>
<li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/12345678900">2025-03-28 02:21:18 CST</a></li>
</code></pre>
</details>

<!-- NONEFLOW -->
"""

    # 模拟评论对象
    mock_comment = mocker.MagicMock()
    mock_comment.body = comment_body

    # 模拟 issue 对象
    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76  # 模拟 artifact 对象
    mock_noneflow_artifact = mocker.MagicMock()
    mock_noneflow_artifact.name = "noneflow"
    mock_noneflow_artifact.id = 123

    mock_other_artifact = mocker.MagicMock()
    mock_other_artifact.name = "other"
    mock_other_artifact.id = 456

    # 模拟 artifacts 响应 - 注意这里应该模拟 parsed_data 的结构
    mock_artifacts_resp = mocker.MagicMock()
    mock_artifacts_resp.parsed_data = mocker.MagicMock()
    mock_artifacts_resp.parsed_data.artifacts = [
        mock_other_artifact,
        mock_noneflow_artifact,
    ]

    # 模拟评论列表，包含自己的评论
    mock_self_comment = mocker.MagicMock()
    mock_self_comment.body = comment_body

    mock_other_comment = mocker.MagicMock()
    mock_other_comment.body = "some other comment"

    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = [mock_other_comment, mock_self_comment]

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments",
                    result=mock_comments_resp,
                ),
                GitHubApi(
                    api="rest.actions.async_list_workflow_run_artifacts",
                    result=mock_artifacts_resp,
                ),
            ],
            snapshot(
                [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                    },
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "run_id": 12345678901,
                    },
                ]
            ),
        )

        result = await get_noneflow_artifact(issue_handler)
        assert result == mock_noneflow_artifact


async def test_get_noneflow_artifact_no_comment(
    app: App, mocker: MockerFixture
) -> None:
    """测试没有评论时的情况"""
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.utils import get_noneflow_artifact
    from src.providers.models import RepoInfo

    # 模拟 issue 对象
    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    # 模拟没有评论的情况 - 返回空列表
    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = []

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments",
                    result=mock_comments_resp,
                ),
            ],
            snapshot(
                [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                    },
                ]
            ),
        )

        with pytest.raises(
            ValueError, match="获取评论失败，无法获取 NoneFlow Artifact"
        ):
            await get_noneflow_artifact(issue_handler)


async def test_get_noneflow_artifact_empty_comment(
    app: App, mocker: MockerFixture
) -> None:
    """测试评论为空时的情况"""
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.utils import get_noneflow_artifact
    from src.providers.models import RepoInfo

    # 模拟 issue 对象
    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    # 模拟空评论对象
    mock_empty_comment = mocker.MagicMock()
    mock_empty_comment.body = None

    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = [mock_empty_comment]

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments",
                    result=mock_comments_resp,
                ),
            ],
            snapshot(
                [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                    },
                ]
            ),
        )

        with pytest.raises(
            ValueError, match="获取评论失败，无法获取 NoneFlow Artifact"
        ):
            await get_noneflow_artifact(issue_handler)


async def test_get_noneflow_artifact_no_history(
    app: App, mocker: MockerFixture
) -> None:
    """测试评论中没有历史工作流信息时的情况"""
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.utils import get_noneflow_artifact
    from src.providers.models import RepoInfo

    # 模拟 issue 对象
    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    # 模拟包含 NONEFLOW 标记但没有历史工作流信息的评论
    comment_body = """
# 📃 商店发布检查结果

没有历史工作流信息

<!-- NONEFLOW -->
"""
    mock_comment = mocker.MagicMock()
    mock_comment.body = comment_body

    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments",
                    result=mock_comments_resp,
                ),
            ],
            snapshot(
                [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                    },
                ]
            ),
        )

        with pytest.raises(ValueError, match="无法从评论中获取历史工作流信息"):
            await get_noneflow_artifact(issue_handler)


async def test_get_noneflow_artifact_no_noneflow_artifact(
    app: App, mocker: MockerFixture
) -> None:
    """测试没有找到 noneflow artifact 时的情况"""
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.utils import get_noneflow_artifact
    from src.providers.models import RepoInfo

    # 模拟 issue 对象
    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76

    # 模拟评论内容，包含历史工作流信息
    comment_body = """
# 📃 商店发布检查结果

<details>
<summary>历史测试</summary>
<pre><code>
<li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/12345678901">2025-03-28 02:22:18 CST</a></li>
</code></pre>
</details>

<!-- NONEFLOW -->
"""
    # 模拟包含历史工作流信息的评论
    mock_comment = mocker.MagicMock()
    mock_comment.body = comment_body

    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = [mock_comment]

    # 模拟只有其他类型的 artifact
    mock_other_artifact = mocker.MagicMock()
    mock_other_artifact.name = "other"
    mock_other_artifact.id = 456

    mock_artifacts_resp = mocker.MagicMock()
    mock_artifacts_resp.parsed_data = mocker.MagicMock()
    mock_artifacts_resp.parsed_data.artifacts = [mock_other_artifact]

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments",
                    result=mock_comments_resp,
                ),
                GitHubApi(
                    api="rest.actions.async_list_workflow_run_artifacts",
                    result=mock_artifacts_resp,
                ),
            ],
            snapshot(
                [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                    },
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "run_id": 12345678901,
                    },
                ]
            ),
        )

        with pytest.raises(ValueError, match="未找到 NoneFlow Artifact"):
            await get_noneflow_artifact(issue_handler)


async def test_get_noneflow_artifact_invalid_run_id(
    app: App, mocker: MockerFixture
) -> None:
    """测试工作流 ID 无效时的情况"""
    from src.plugins.github.handlers import IssueHandler
    from src.plugins.github.plugins.publish.utils import get_noneflow_artifact
    from src.providers.models import RepoInfo

    # 模拟 issue 对象
    mock_issue = mocker.MagicMock(spec=Issue)
    mock_issue.number = 76  # 模拟评论内容，包含无效的工作流 ID
    comment_body = """
# 📃 商店发布检查结果

<details>
<summary>历史测试</summary>
<pre><code>
<li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/invalid">2025-03-28 02:22:18 CST</a></li>
</code></pre>
</details>

<!-- NONEFLOW -->
"""
    # 模拟包含无效工作流 ID 的评论
    mock_comment = mocker.MagicMock()
    mock_comment.body = comment_body

    mock_comments_resp = mocker.MagicMock()
    mock_comments_resp.parsed_data = [mock_comment]

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)

        issue_handler = IssueHandler(
            bot=bot,
            repo_info=RepoInfo(owner="owner", repo="repo"),
            issue=mock_issue,
        )

        should_call_apis(
            ctx,
            [
                GitHubApi(
                    api="rest.issues.async_list_comments",
                    result=mock_comments_resp,
                ),
            ],
            snapshot(
                [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "issue_number": 76,
                    },
                ]
            ),
        )

        with pytest.raises(ValueError, match="无法从评论中获取历史工作流信息"):
            await get_noneflow_artifact(issue_handler)
