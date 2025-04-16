from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockFixture

from tests.providers.validation.utils import generate_plugin_data


async def test_render_data_bot(app: App):
    """机器人验证数据"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import BotPublishInfo, PublishType, ValidationDict

    raw_data = {
        "name": "CoolQBot",
        "desc": "基于 NoneBot2 的聊天机器人",
        "author": "he0119",
        "author_id": 1,
        "homepage": "https://github.com/he0119/CoolQBot",
        "tags": [],
        "is_official": False,
    }
    result = ValidationDict(
        type=PublishType.BOT,
        raw_data=raw_data,
        valid_data=raw_data,
        info=BotPublishInfo.model_construct(**raw_data),
        errors=[],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Bot: CoolQBot

[![主页](https://img.shields.io/badge/HOMEPAGE-https://github.com/he0119/CoolQBot-green?style=for-the-badge)](https://github.com/he0119/CoolQBot)

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://github.com/he0119/CoolQBot">主页</a> 返回状态码 200。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )

    raw_data = {
        "name": "March7th",
        "desc": "三月七 - 崩坏：星穹铁道机器人",
        "author": "mobyw",
        "author_id": 1,
        "homepage": "https://github.com/Mar-7th/March7th",
        "tags": [
            {"label": "StarRail", "color": "#5a8ccc"},
            {"label": "星穹铁道", "color": "#6faec6"},
        ],
        "is_official": False,
    }
    result = ValidationDict(
        type=PublishType.BOT,
        raw_data=raw_data,
        valid_data=raw_data,
        info=BotPublishInfo.model_construct(**raw_data),
        errors=[],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Bot: March7th

[![主页](https://img.shields.io/badge/HOMEPAGE-https://github.com/Mar-7th/March7th-green?style=for-the-badge)](https://github.com/Mar-7th/March7th)

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://github.com/Mar-7th/March7th">主页</a> 返回状态码 200。</li><li>✅ 标签: StarRail-#5a8ccc, 星穹铁道-#6faec6。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )


async def test_render_data_adapter(app: App):
    """适配器数据"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import AdapterPublishInfo, PublishType, ValidationDict

    raw_data = {
        "module_name": "nonebot.adapters.villa",
        "project_link": "nonebot-adapter-villa",
        "name": "大别野",
        "desc": "米游社大别野官方Bot适配",
        "author": "CMHopeSunshine",
        "author_id": 1,
        "homepage": "https://github.com/CMHopeSunshine/nonebot-adapter-villa",
        "tags": [{"label": "米哈游", "color": "#e10909"}],
        "is_official": False,
        "time": "2023-12-21T06:57:44.318894Z",
        "version": "1.4.2",
    }
    result = ValidationDict(
        type=PublishType.ADAPTER,
        raw_data=raw_data,
        valid_data=raw_data,
        info=AdapterPublishInfo.model_construct(**raw_data),
        errors=[],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Adapter: 大别野

[![主页](https://img.shields.io/badge/HOMEPAGE-https://github.com/CMHopeSunshine/nonebot-adapter-villa-green?style=for-the-badge)](https://github.com/CMHopeSunshine/nonebot-adapter-villa)

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://github.com/CMHopeSunshine/nonebot-adapter-villa">主页</a> 返回状态码 200。</li><li>✅ 项目 <a href="https://pypi.org/project/nonebot-adapter-villa/">nonebot-adapter-villa</a> 已发布至 PyPI。</li><li>✅ 标签: 米哈游-#e10909。</li><li>✅ 版本号: 1.4.2。</li><li>✅ 发布时间：2023-12-21 14:57:44 CST。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )


async def test_render_data_plugin(app: App, mocker: MockFixture):
    """插件数据"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import PluginPublishInfo, PublishType, ValidationDict

    raw_data = {
        "module_name": "nonebot_plugin_treehelp",
        "project_link": "nonebot-plugin-treehelp",
        "name": "帮助",
        "desc": "获取插件帮助信息",
        "author": "he0119",
        "author_id": 1,
        "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
        "tags": [{"label": "render", "color": "#ffffff"}],
        "is_official": False,
        "type": "application",
        "supported_adapters": None,
        "load": True,
        "skip_test": False,
        "time": "2024-07-13T04:41:40.905441Z",
        "version": "0.5.0",
    }
    result = ValidationDict(
        type=PublishType.PLUGIN,
        raw_data=raw_data,
        valid_data=raw_data,
        info=PluginPublishInfo.model_construct(**raw_data),
        errors=[],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Plugin: 帮助

[![主页](https://img.shields.io/badge/HOMEPAGE-https://github.com/he0119/nonebot-plugin-treehelp-green?style=for-the-badge)](https://github.com/he0119/nonebot-plugin-treehelp) [![测试结果](https://img.shields.io/badge/RESULT-OK-green?style=for-the-badge)](https://github.com/owner/repo/actions/runs/123456)

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://github.com/he0119/nonebot-plugin-treehelp">主页</a> 返回状态码 200。</li><li>✅ 项目 <a href="https://pypi.org/project/nonebot-plugin-treehelp/">nonebot-plugin-treehelp</a> 已发布至 PyPI。</li><li>✅ 标签: render-#ffffff。</li><li>✅ 插件类型: application。</li><li>✅ 插件支持的适配器: 所有。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li><li>✅ 版本号: 0.5.0。</li><li>✅ 发布时间：2024-07-13 12:41:40 CST。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )


async def test_render_data_plugin_supported_adapters(app: App, mocker: MockFixture):
    """插件支持的适配器"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import PluginPublishInfo, PublishType, ValidationDict

    result = ValidationDict(
        type=PublishType.PLUGIN,
        raw_data={
            "name": "帮助",
            "load": True,
            "skip_test": False,
        },
        valid_data={
            "supported_adapters": [
                "nonebot.adapters.onebot.v11",
                "nonebot.adapters.none",
            ],
            "load": True,
            "skip_test": False,
        },
        info=PluginPublishInfo.model_construct(**generate_plugin_data()),
        errors=[],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Plugin: 帮助

[![测试结果](https://img.shields.io/badge/RESULT-OK-green?style=for-the-badge)](https://github.com/owner/repo/actions/runs/123456)

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 插件支持的适配器: nonebot.adapters.onebot.v11, nonebot.adapters.none。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )
