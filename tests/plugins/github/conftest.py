import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_installation(mocker: MockerFixture):
    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation
    return mock_installation_resp


@pytest.fixture
def mock_installation_token(mocker: MockerFixture):
    mock_token = mocker.MagicMock()
    mock_token.token = "test-token"
    mock_token_resp = mocker.MagicMock()
    mock_token_resp.parsed_data = mock_token
    return mock_token_resp
