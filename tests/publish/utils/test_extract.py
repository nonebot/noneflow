from nonebug import App


async def test_extract_name_from_title(app: App):
    from src.plugins.publish.utils import extract_name_from_title
    from src.utils.validation import PublishType

    assert extract_name_from_title("Adapter: test", PublishType.ADAPTER) == "test"
    assert extract_name_from_title("Bot: test", PublishType.BOT) == "test"
    assert extract_name_from_title("Plugin: test", PublishType.PLUGIN) == "test"
    assert extract_name_from_title("Plugin: test", PublishType.BOT) is None
