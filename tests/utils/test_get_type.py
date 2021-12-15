from pytest_mock import MockerFixture

from src.models import PublishType
from src.utils import get_type_by_commit_message, get_type_by_labels, get_type_by_title


def test_get_type_by_labels(mocker: MockerFixture):
    mock_label = mocker.MagicMock()  # type: ignore
    mock_label.name = "Bot"

    publish_type = get_type_by_labels([mock_label])

    assert publish_type == PublishType.BOT


def test_get_type_by_labels_wrong(mocker: MockerFixture):
    mock_label = mocker.MagicMock()  # type: ignore
    mock_label.name = "Something"

    publish_type = get_type_by_labels([mock_label])

    assert publish_type is None


def test_get_type_by_title():
    title = "Bot: test"
    publish_type = get_type_by_title(title)

    assert publish_type == PublishType.BOT


def test_get_type_by_title_wrong():
    title = "Something: test"
    publish_type = get_type_by_title(title)

    assert publish_type is None


def test_get_type_by_commit_message():
    message = ":beers: publish bot test"

    publish_type = get_type_by_commit_message(message)

    assert publish_type == PublishType.BOT


def test_get_type_by_commit_message_wrong():
    message = "Something: publish bot test"

    publish_type = get_type_by_commit_message(message)

    assert publish_type is None
