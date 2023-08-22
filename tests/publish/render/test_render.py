from nonebug import App


async def test_render_empty(app: App):
    """测试没有数据和错误时的输出"""
    from src.plugins.publish.render import render_comment
    from src.utils.validation import PublishType, ValidationDict

    result: ValidationDict = {
        "type": PublishType.BOT,
        "name": "name",
        "valid": True,
        "data": {},
        "errors": [],
        "author": "author",
    }

    comment = await render_comment(result)
    assert (
        comment
        == "# 📃 商店发布检查结果\n\n> Bot: name\n\n**✅ 所有测试通过，一切准备就绪！**\n\n\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n"
    )

    comment = await render_comment(result, True)
    assert (
        comment
        == "# 📃 商店发布检查结果\n\n> Bot: name\n\n**✅ 所有测试通过，一切准备就绪！**\n\n\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n♻️ 评论已更新至最新检查结果\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n"
    )
