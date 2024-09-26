from typing import cast

from nonebot import get_adapter
from nonebot.adapters.github import Adapter, GitHubBot
from nonebot.adapters.github.config import GitHubApp
from nonebug import App
from pytest_mock import MockerFixture


async def test_get_pull_requests_by_label(app: App, mocker: MockerFixture) -> None:
    """测试获取指定标签的拉取请求"""
    from src.plugins.github.plugins.publish.depends import get_pull_requests_by_label
    from src.plugins.github.models import RepoInfo
    from src.providers.validation.models import PublishType

    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"

    mock_pull = mocker.MagicMock()
    mock_pull.labels = [mock_label]

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

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
    from src.plugins.github.models import RepoInfo
    from src.providers.validation.models import PublishType

    mock_label = mocker.MagicMock()
    mock_label.name = "Some"

    mock_pull = mocker.MagicMock()
    mock_pull.labels = [mock_label]

    mock_pulls_resp = mocker.MagicMock()
    mock_pulls_resp.parsed_data = [mock_pull]

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=GitHubBot,
            adapter=adapter,
            self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
        )
        bot = cast(GitHubBot, bot)

        ctx.should_call_api(
            "rest.pulls.async_list",
            {"owner": "owner", "repo": "repo", "state": "open"},
            mock_pulls_resp,
        )

        pulls = await get_pull_requests_by_label(
            bot, RepoInfo(owner="owner", repo="repo"), PublishType.BOT
        )
        assert pulls == []
