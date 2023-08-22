from nonebug import App
from pytest_mock import MockFixture


async def test_render_data_bot(app: App):
    """渲染机器人验证数据"""
    from src.plugins.publish.render import render_comment
    from src.utils.validation import PublishType, ValidationDict

    result: ValidationDict = {
        "valid": True,
        "data": {
            "name": "CoolQBot",
            "desc": "基于 NoneBot2 的聊天机器人",
            "author": "he0119",
            "homepage": "https://github.com/he0119/CoolQBot",
            "tags": [],
            "is_official": False,
        },
        "errors": [],
        "type": PublishType.BOT,
        "name": "CoolQBot",
        "author": "he0119",
    }

    comment = await render_comment(result)
    assert (
        comment
        == """# 📃 商店发布检查结果\n\n> Bot: CoolQBot\n\n**✅ 所有测试通过，一切准备就绪！**\n\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ 项目 <a href="https://github.com/he0119/CoolQBot">主页</a> 返回状态码 200。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n"""
    )

    result: ValidationDict = {
        "valid": True,
        "data": {
            "name": "March7th",
            "desc": "三月七 - 崩坏：星穹铁道机器人",
            "author": "mobyw",
            "homepage": "https://github.com/Mar-7th/March7th",
            "tags": [
                {"label": "StarRail", "color": "#5a8ccc"},
                {"label": "星穹铁道", "color": "#6faec6"},
            ],
            "is_official": False,
        },
        "errors": [],
        "type": PublishType.BOT,
        "name": "March7th",
        "author": "mobyw",
    }

    comment = await render_comment(result)
    assert (
        comment
        == """# 📃 商店发布检查结果\n\n> Bot: March7th\n\n**✅ 所有测试通过，一切准备就绪！**\n\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ 项目 <a href="https://github.com/Mar-7th/March7th">主页</a> 返回状态码 200。</li><li>✅ 标签: StarRail-#5a8ccc, 星穹铁道-#6faec6。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n"""
    )


async def test_render_data_adapter(app: App):
    """渲染适配器数据"""
    from src.plugins.publish.render import render_comment
    from src.utils.validation import PublishType, ValidationDict

    result: ValidationDict = {
        "valid": True,
        "data": {
            "module_name": "nonebot.adapters.villa",
            "project_link": "nonebot-adapter-villa",
            "name": "大别野",
            "desc": "米游社大别野官方Bot适配",
            "author": "CMHopeSunshine",
            "homepage": "https://github.com/CMHopeSunshine/nonebot-adapter-villa",
            "tags": [{"label": "米哈游", "color": "#e10909"}],
            "is_official": False,
        },
        "errors": [],
        "type": PublishType.ADAPTER,
        "name": "大别野",
        "author": "CMHopeSunshine",
    }

    comment = await render_comment(result)
    assert (
        comment
        == """# 📃 商店发布检查结果\n\n> Adapter: 大别野\n\n**✅ 所有测试通过，一切准备就绪！**\n\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ 项目 <a href="https://pypi.org/project/nonebot-adapter-villa/">nonebot-adapter-villa</a> 已发布至 PyPI。</li><li>✅ 项目 <a href="https://github.com/CMHopeSunshine/nonebot-adapter-villa">主页</a> 返回状态码 200。</li><li>✅ 标签: 米哈游-#e10909。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n"""
    )


async def test_render_data_plugin(app: App, mocker: MockFixture):
    """渲染插件数据"""
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.render import render_comment
    from src.utils.validation import PublishType, ValidationDict

    mocker.patch.object(plugin_config, "plugin_test_result", True)

    result: ValidationDict = {
        "valid": True,
        "data": {
            "module_name": "nonebot_plugin_treehelp",
            "project_link": "nonebot-plugin-treehelp",
            "name": "帮助",
            "desc": "获取插件帮助信息",
            "author": "he0119",
            "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
            "tags": [],
            "is_official": False,
            "type": "application",
            "supported_adapters": None,
        },
        "errors": [],
        "type": PublishType.PLUGIN,
        "name": "帮助",
        "author": "he0119",
    }

    comment = await render_comment(result)
    assert (
        comment
        == """# 📃 商店发布检查结果\n\n> Plugin: 帮助\n\n**✅ 所有测试通过，一切准备就绪！**\n\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ 项目 <a href="https://pypi.org/project/nonebot-plugin-treehelp/">nonebot-plugin-treehelp</a> 已发布至 PyPI。</li><li>✅ 项目 <a href="https://github.com/he0119/nonebot-plugin-treehelp">主页</a> 返回状态码 200。</li><li>✅ 插件类型: application。</li><li>✅ 插件支持的适配器: 所有。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n"""
    )
