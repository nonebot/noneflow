from nonebug import App


async def test_strip_ansi(app: App):
    from src.utils.plugin_test import strip_ansi

    assert strip_ansi("test") == "test"

    assert (
        strip_ansi(
            "插件 nonebot-plugin-status 的信息如下： [34mname[39m         : [36mnonebot-plugin-status[39m"
        )
        == "插件 nonebot-plugin-status 的信息如下： name         : nonebot-plugin-status"
    )
