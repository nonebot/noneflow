from inline_snapshot import snapshot
from nonebug import App

from tests.providers.validation.utils import generate_bot_data


async def test_render_empty(app: App):
    """测试没有数据和错误时的输出"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import BotPublishInfo, PublishType, ValidationDict

    result = ValidationDict(
        type=PublishType.BOT,
        raw_data={"name": "name"},
        info=BotPublishInfo.model_construct(**generate_bot_data()),
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Bot: name

**✅ 所有测试通过，一切准备就绪！**



---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )


async def test_render_reuse(app: App):
    """复用评论"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import BotPublishInfo, PublishType, ValidationDict

    result = ValidationDict(
        type=PublishType.BOT,
        raw_data={"name": "name"},
        info=BotPublishInfo.model_construct(**generate_bot_data()),
    )

    comment = await render_comment(result, True)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Bot: name

**✅ 所有测试通过，一切准备就绪！**



---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )
