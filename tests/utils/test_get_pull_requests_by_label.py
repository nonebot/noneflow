# from pytest_mock import MockerFixture


# def test_get_pull_requests_by_label(mocker: MockerFixture) -> None:
#     """测试获取指定标签的拉取请求"""
#     from src import Bot

#     bot = Bot()
#     bot.github = mocker.MagicMock()

#     mock_label = mocker.MagicMock()
#     mock_label.name = "Bot"

#     mock_pull = mocker.MagicMock()
#     mock_pull.labels = [mock_label]

#     mock_pulls_resp = mocker.MagicMock()
#     mock_pulls_resp.parsed_data = [mock_pull]
#     bot.github.rest.pulls.list.return_value = mock_pulls_resp

#     pulls = bot.get_pull_requests_by_label("Bot")

#     bot.github.rest.pulls.list.assert_called_with("owner", "repo", state="open")
#     assert pulls[0] == mock_pull


# def test_get_pull_requests_by_label_not_match(mocker: MockerFixture) -> None:
#     """测试获取指定标签的拉取请求，但是没有匹配的"""
#     from src import Bot

#     bot = Bot()
#     bot.github = mocker.MagicMock()

#     mock_label = mocker.MagicMock()
#     mock_label.name = "Some"

#     mock_pull = mocker.MagicMock()
#     mock_pull.labels = [mock_label]

#     mock_pulls_resp = mocker.MagicMock()
#     mock_pulls_resp.parsed_data = [mock_pull]
#     bot.github.rest.pulls.list.return_value = mock_pulls_resp

#     pulls = bot.get_pull_requests_by_label("Bot")

#     bot.github.rest.pulls.list.assert_called_with("owner", "repo", state="open")
#     assert pulls == []
