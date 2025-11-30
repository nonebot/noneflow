from nonebug import App
from pytest_mock import MockerFixture

from tests.plugins.github.utils import get_github_bot


async def test_get_pull_requests_by_label(app: App, mocker: MockerFixture) -> None:
    """测试获取指定标签的拉取请求"""
    from src.plugins.github.plugins.publish.depends import get_pull_requests_by_label
    from src.providers.models import RepoInfo
    from src.providers.validation.models import PublishType

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"

    mock_pull = mocker.MagicMock()
    mock_pull.labels = [mock_label]

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)

        ctx.should_call_api(
            "rest.pulls.async_list",
            {"owner": "owner", "repo": "repo", "state": "open"},
            mock_pulls_resp,
        )

        pulls = await get_pull_requests_by_label(
            bot, RepoInfo(owner="owner", repo="repo"), PublishType.BOT
        )
        assert pulls[0] == mock_pull


async def test_get_pull_requests_by_label_not_match(
    app: App, mocker: MockerFixture
) -> None:
    """测试获取指定标签的拉取请求，但是没有匹配的"""
    from src.plugins.github.plugins.publish.depends import get_pull_requests_by_label
    from src.providers.models import RepoInfo
    from src.providers.validation.models import PublishType

    mock_label = mocker.MagicMock()
    mock_label.name = "Some"

    mock_pull = mocker.MagicMock()
    mock_pull.labels = [mock_label]

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    async with app.test_api() as ctx:
        _adapter, bot = get_github_bot(ctx)

        ctx.should_call_api(
            "rest.pulls.async_list",
            {"owner": "owner", "repo": "repo", "state": "open"},
            mock_pulls_resp,
        )

        pulls = await get_pull_requests_by_label(
            bot, RepoInfo(owner="owner", repo="repo"), PublishType.BOT
        )
        assert pulls == []
