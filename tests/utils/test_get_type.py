from pytest_mock import MockerFixture

from src.models import PublishType
from src.utils import get_type_by_commit_message, get_type_by_labels, get_type_by_title


def test_get_type_by_labels(mocker: MockerFixture):
    """通过标签获取发布类型"""
    mock_label = mocker.MagicMock()
    mock_label.name = "Bot"

    publish_type = get_type_by_labels([mock_label])

    assert publish_type == PublishType.BOT

    mock_label.name = "Plugin"

    publish_type = get_type_by_labels([mock_label])

    assert publish_type == PublishType.PLUGIN

    mock_label.name = "Adapter"

    publish_type = get_type_by_labels([mock_label])

    assert publish_type == PublishType.ADAPTER


def test_get_type_by_labels_wrong(mocker: MockerFixture):
    mock_label = mocker.MagicMock()
    mock_label.name = "Something"

    publish_type = get_type_by_labels([mock_label, "Something"])

    assert publish_type is None


def test_get_type_by_title():
    """通过标题获取发布类型"""
    title = "Bot: test"
    publish_type = get_type_by_title(title)

    assert publish_type == PublishType.BOT

    title = "Adapter: test"
    publish_type = get_type_by_title(title)

    assert publish_type == PublishType.ADAPTER

    title = "Plugin: test"
    publish_type = get_type_by_title(title)

    assert publish_type == PublishType.PLUGIN


def test_get_type_by_title_wrong():
    title = "Something: test"
    publish_type = get_type_by_title(title)

    assert publish_type is None


def test_get_type_by_commit_message():
    """通过提交信息获取发布类型"""
    message = ":beers: publish bot test"

    publish_type = get_type_by_commit_message(message)

    assert publish_type == PublishType.BOT

    message = ":beers: publish adapter test"

    publish_type = get_type_by_commit_message(message)

    assert publish_type == PublishType.ADAPTER

    message = ":beers: publish plugin test"

    publish_type = get_type_by_commit_message(message)

    assert publish_type == PublishType.PLUGIN


def test_get_type_by_commit_message_wrong():
    message = "Something: publish bot test"

    publish_type = get_type_by_commit_message(message)

    assert publish_type is None
