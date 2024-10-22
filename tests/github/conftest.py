import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_installation(mocker: MockerFixture):
    mock_installation = mocker.MagicMock()
    mock_installation.id = 123
    mock_installation_resp = mocker.MagicMock()
    mock_installation_resp.parsed_data = mock_installation
    return mock_installation_resp
