from nonebug import App
from pytest_mock import MockFixture


async def test_render_error_bot(app: App):
    """渲染机器人验证数据"""
    from src.plugins.publish.render import render_comment
    from src.utils.validation import PublishType, ValidationDict

    result: ValidationDict = {
        "valid": False,
        "data": {
            "desc": "基于 NoneBot2 的聊天机器人",
            "author": "he0119",
            "is_official": False,
        },
        "errors": [
            {
                "loc": ("name",),
                "msg": "名称不能超过 50 个字符。",
                "type": "value_error.name.too_long",
                "input": "tooooooooooooooooooooooooooooooooooooooooooooooooog",
            },
            {
                "loc": ("homepage",),
                "msg": "项目主页不可访问。",
                "type": "value_error.homepage.unreachable",
                "ctx": {"status_code": 404},
                "input": "https://www.baidu.com",
            },
            {
                "loc": ("tags", 1, "label"),
                "msg": "标签名称超过 10 个字符。",
                "type": "value_error.tag.label",
                "input": "testtoolong",
            },
            {
                "loc": ("tags", 1, "color"),
                "msg": "标签颜色不符合十六进制颜色码规则。",
                "type": "value_error.tag.color",
                "input": "#fffffff",
            },
        ],
        "type": PublishType.BOT,
        "name": "CoolQBot",
        "author": "he0119",
    }

    comment = await render_comment(result)
    assert (
        comment
        == """# 📃 商店发布检查结果\n\n> Bot: CoolQBot\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n\n<pre><code><li>⚠️ 名称过长。<dt>请确保名称不超过 50 个字符。</dt></li><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保你的项目主页可访问。</dt></li><li>⚠️ 第 2 个标签名称过长<dt>请确保标签名称不超过 10 个字符。</dt></li><li>⚠️ 第 2 个标签颜色错误<dt>请确保标签颜色符合十六进制颜色码规则。</dt></li></code></pre>\n\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n"""
    )


async def test_render_error_adapter(app: App):
    """渲染适配器数据"""
    from src.plugins.publish.render import render_comment
    from src.utils.validation import PublishType, ValidationDict

    result: ValidationDict = {
        "valid": False,
        "data": {
            "module_name": "nonebot.adapters.villa",
            "project_link": "nonebot-adapter-villa",
            "desc": "米游社大别野官方Bot适配",
            "author": "CMHopeSunshine",
            "is_official": False,
        },
        "errors": [
            {
                "loc": ("module_name",),
                "msg": "包名不符合规范。",
                "type": "value_error.module_name",
                "input": "module_name/",
            },
            {
                "loc": ("project_link",),
                "msg": "PyPI 项目名不存在。",
                "type": "value_error.project_link.not_found",
                "input": "project_link_failed",
            },
            {
                "loc": ("name",),
                "msg": "名称不能超过 50 个字符。",
                "type": "value_error.name.too_long",
                "input": "tooooooooooooooooooooooooooooooooooooooooooooooooog",
            },
            {
                "loc": ("homepage",),
                "msg": "项目主页不可访问。",
                "type": "value_error.homepage.unreachable",
                "ctx": {"status_code": 404},
                "input": "https://www.baidu.com",
            },
            {
                "loc": ("tags", 1, "label"),
                "msg": "标签名称超过 10 个字符。",
                "type": "value_error.tag.label",
                "input": "testtoolong",
            },
            {
                "loc": ("tags", 1, "color"),
                "msg": "标签颜色不符合十六进制颜色码规则。",
                "type": "value_error.tag.color",
                "input": "#fffffff",
            },
        ],
        "type": PublishType.ADAPTER,
        "name": "大别野",
        "author": "CMHopeSunshine",
    }

    comment = await render_comment(result)
    assert (
        comment
        == """# 📃 商店发布检查结果\n\n> Adapter: 大别野\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n\n<pre><code><li>⚠️ 包名 module_name/ 不符合规范。<dt>请确保包名正确。</dt></li><li>⚠️ 项目 <a href="https://pypi.org/project/project_link_failed/">project_link_failed</a> 未发布至 PyPI。<dt>请将你的项目发布至 PyPI。</dt></li><li>⚠️ 名称过长。<dt>请确保名称不超过 50 个字符。</dt></li><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保你的项目主页可访问。</dt></li><li>⚠️ 第 2 个标签名称过长<dt>请确保标签名称不超过 10 个字符。</dt></li><li>⚠️ 第 2 个标签颜色错误<dt>请确保标签颜色符合十六进制颜色码规则。</dt></li></code></pre>\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ 项目 <a href="https://pypi.org/project/nonebot-adapter-villa/">nonebot-adapter-villa</a> 已发布至 PyPI。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n"""
    )


async def test_render_error_plugin(app: App, mocker: MockFixture):
    """渲染插件数据"""
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.render import render_comment
    from src.utils.validation import PublishType, ValidationDict

    mocker.patch.object(plugin_config, "plugin_test_result", True)
    mocker.patch.object(plugin_config, "plugin_test_metadata", {})

    result: ValidationDict = {
        "valid": False,
        "data": {
            "name": "帮助",
            "desc": "获取插件帮助信息",
            "author": "he0119",
            "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
            "tags": [],
            "is_official": False,
        },
        "errors": [
            {
                "loc": ("__root__",),
                "msg": "PyPI 项目名 project_link 加包名 module_name 的值与商店重复。",
                "type": "value_error.duplication",
                "ctx": {"project_link": "project_link", "module_name": "module_name"},
            },
            {
                "loc": ("name",),
                "msg": "名称不能超过 50 个字符。",
                "type": "value_error.name.too_long",
                "input": "tooooooooooooooooooooooooooooooooooooooooooooooooog",
            },
            {
                "loc": ("homepage",),
                "msg": "项目主页不可访问。",
                "type": "value_error.homepage.unreachable",
                "ctx": {"status_code": 404},
                "input": "https://www.baidu.com",
            },
            {
                "loc": ("tags", 1, "label"),
                "msg": "标签名称超过 10 个字符。",
                "type": "value_error.tag.label",
                "input": "testtoolong",
            },
            {
                "loc": ("tags", 1, "color"),
                "msg": "标签颜色不符合十六进制颜色码规则。",
                "type": "value_error.tag.color",
                "input": "#fffffff",
            },
            {
                "loc": ("type",),
                "msg": "field required",
                "type": "value_error.missing",
            },
        ],
        "type": PublishType.PLUGIN,
        "name": "帮助",
        "author": "he0119",
    }

    comment = await render_comment(result)
    assert (
        comment
        == """# 📃 商店发布检查结果\n\n> Plugin: 帮助\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n\n<pre><code><li>⚠️ PyPI 项目名 project_link 加包名 module_name 的值与商店重复。<dt>请确保没有重复发布。</dt></li><li>⚠️ 名称过长。<dt>请确保名称不超过 50 个字符。</dt></li><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保你的项目主页可访问。</dt></li><li>⚠️ 第 2 个标签名称过长<dt>请确保标签名称不超过 10 个字符。</dt></li><li>⚠️ 第 2 个标签颜色错误<dt>请确保标签颜色符合十六进制颜色码规则。</dt></li><li>⚠️ 插件类型: 无法匹配到数据。<dt>请确保填写该项目。</dt></li></code></pre>\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ 项目 <a href="https://github.com/he0119/nonebot-plugin-treehelp">主页</a> 返回状态码 200。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n"""
    )


async def test_render_error_plugin_load_test(app: App, mocker: MockFixture):
    """渲染插件数据"""
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.render import render_comment
    from src.utils.validation import PublishType, ValidationDict

    mocker.patch.object(plugin_config, "plugin_test_result", False)
    mocker.patch.object(plugin_config, "plugin_test_output", "output")

    result: ValidationDict = {
        "valid": False,
        "data": {
            "name": "帮助",
            "desc": "获取插件帮助信息",
            "author": "he0119",
            "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
            "tags": [],
            "is_official": False,
        },
        "errors": [],
        "type": PublishType.PLUGIN,
        "name": "帮助",
        "author": "he0119",
    }

    comment = await render_comment(result)
    assert (
        comment
        == """# 📃 商店发布检查结果\n\n> Plugin: 帮助\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n\n<pre><code><li>⚠️ 无法获取到插件元数据。<dt>请确保插件正常加载。</dt></li><li>⚠️ 插件加载测试未通过。\n<details>\n  <summary>测试输出</summary>\n  output\n</details></li></code></pre>\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ 项目 <a href="https://github.com/he0119/nonebot-plugin-treehelp">主页</a> 返回状态码 200。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n"""
    )


async def test_render_error_plugin_metadata(app: App, mocker: MockFixture):
    """渲染插件数据，缺少元数据的情况"""
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.render import render_comment
    from src.utils.validation import PublishType, ValidationDict

    mocker.patch.object(plugin_config, "plugin_test_result", True)

    result: ValidationDict = {
        "valid": False,
        "data": {
            "author": "he0119",
            "tags": [],
            "is_official": False,
        },
        "errors": [
            {
                "loc": ("name",),
                "msg": "field required",
                "type": "value_error.missing",
            },
            {
                "loc": ("desc",),
                "msg": "field required",
                "type": "value_error.missing",
            },
            {
                "loc": ("homepage",),
                "msg": "field required",
                "type": "value_error.missing",
            },
            {
                "loc": ("type",),
                "msg": "field required",
                "type": "value_error.missing",
            },
        ],
        "type": PublishType.PLUGIN,
        "name": "帮助",
        "author": "he0119",
    }

    comment = await render_comment(result)
    assert (
        comment
        == """# 📃 商店发布检查结果\n\n> Plugin: 帮助\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n\n<pre><code><li>⚠️ 无法获取到插件元数据。<dt>请填写插件元数据。</dt></li></code></pre>\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->\n"""
    )
