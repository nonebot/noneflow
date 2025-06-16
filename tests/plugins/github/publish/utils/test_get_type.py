from pytest_mock import MockerFixture


async def test_get_type_by_labels(mocker: MockerFixture):
    """通过标签获取发布类型"""
    from src.plugins.github.depends.utils import get_type_by_labels
    from src.providers.validation.models import PublishType

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


async def test_get_type_by_labels_wrong(mocker: MockerFixture):
    from src.plugins.github.depends.utils import get_type_by_labels

    mock_label = mocker.MagicMock()
    mock_label.name = "Something"

    publish_type = get_type_by_labels([mock_label, "Something"])

    assert publish_type is None


async def test_get_type_by_title():
    """通过标题获取发布类型"""
    from src.plugins.github.plugins.publish.utils import get_type_by_title
    from src.providers.validation.models import PublishType

    title = "Bot: test"
    publish_type = get_type_by_title(title)

    assert publish_type == PublishType.BOT

    title = "Adapter: test"
    publish_type = get_type_by_title(title)

    assert publish_type == PublishType.ADAPTER

    title = "Plugin: test"
    publish_type = get_type_by_title(title)

    assert publish_type == PublishType.PLUGIN


async def test_get_type_by_title_wrong():
    from src.plugins.github.plugins.publish.utils import get_type_by_title

    title = "Something: test"
    publish_type = get_type_by_title(title)

    assert publish_type is None


async def test_get_type_by_commit_message():
    """通过提交信息获取发布类型"""
    from src.plugins.github.plugins.publish.utils import get_type_by_commit_message
    from src.providers.validation.models import PublishType

    message = ":beers: publish bot test"

    publish_type = get_type_by_commit_message(message)

    assert publish_type == PublishType.BOT

    message = ":beers: publish adapter test"

    publish_type = get_type_by_commit_message(message)

    assert publish_type == PublishType.ADAPTER

    message = ":beers: publish plugin test"

    publish_type = get_type_by_commit_message(message)

    assert publish_type == PublishType.PLUGIN


async def test_get_type_by_commit_message_wrong():
    from src.plugins.github.plugins.publish.utils import get_type_by_commit_message

    message = "Something: publish bot test"

    publish_type = get_type_by_commit_message(message)

    assert publish_type is None
