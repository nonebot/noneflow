from nonebug import App
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.publish.utils import (
    generate_issue_body_adapter,
    generate_issue_body_bot,
    generate_issue_body_plugin,
    generate_issue_body_plugin_skip_test,
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
    from src.plugins.github.plugins.publish.validation import (
        validate_plugin_info_from_issue,
    )
    from src.plugins.github import plugin_config

    mocker.patch.object(plugin_config, "skip_plugin_test", True)

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_plugin_skip_test()
    mock_issue.user.login = "test"

    result = await validate_plugin_info_from_issue(mock_issue)

    assert result.valid
    assert mocked_api["homepage"].called


# async def test_validate_info_from_issue_plugin_metadata(
#     app: App, mocker: MockerFixture, mocked_api: MockRouter
# ):
#     from src.plugins.github.plugins.publish.validation import validate_plugin_info_from_issue
#     from src.plugins.github import plugin_config

#     mocker.patch.object(plugin_config, "skip_plugin_test", True)
#     mocker.patch.object(
#         plugin_config,
#         "plugin_test_metadata",
#         {
#             "name": "name",
#             "description": "description",
#             "homepage": "https://nonebot.dev",
#             "type": "application",
#             "supported_adapters": None,
#         },
#     )
#     mock_issue = mocker.MagicMock()
#     mock_issue.body = generate_issue_body_plugin()
#     mock_issue.user.login = "test"

#     result = await validate_plugin_info_from_issue(mock_issue)

#     assert result.valid
#     assert mocked_api["homepage"].called


# async def test_validate_info_from_issue_plugin_metadata_missing(
#     app: App, mocker: MockerFixture, mocked_api: MockRouter
# ):
#     from src.plugins.github.plugins.publish.validation import validate_plugin_info_from_issue

#     mock_issue = mocker.MagicMock()
#     mock_issue.body = generate_issue_body_plugin()
#     mock_issue.user.login = "test"

#     result = await validate_plugin_info_from_issue(mock_issue)

#     assert not result.valid
#     assert not mocked_api["homepage"].called
