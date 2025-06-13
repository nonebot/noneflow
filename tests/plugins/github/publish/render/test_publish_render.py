from datetime import datetime

from inline_snapshot import snapshot
from nonebug import App

from tests.providers.validation.utils import generate_bot_data, generate_plugin_data


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


async def test_render_history(app: App):
    """测试历史记录渲染，包括排序和数量限制"""

    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.constants import TIME_ZONE
    from src.providers.validation import (
        PluginPublishInfo,
        PublishType,
        ValidationDict,
    )

    # 创建多个历史记录用于测试排序和数量限制
    history = [
        (
            False,
            "https://github.com/nonebot/nonebot2/actions/runs/14156878700",
            datetime(2020, 10, 2, 12, 0, 18, tzinfo=TIME_ZONE),
        ),
        (
            True,
            "https://github.com/nonebot/nonebot2/actions/runs/14156878699",
            datetime(2020, 10, 1, 12, 0, 18, tzinfo=TIME_ZONE),
        ),
        (
            True,
            "https://github.com/nonebot/nonebot2/actions/runs/14156878701",
            datetime(2020, 10, 3, 12, 0, 18, tzinfo=TIME_ZONE),
        ),
        (
            True,
            "https://github.com/nonebot/nonebot2/actions/runs/14156878702",
            datetime(2020, 10, 4, 12, 0, 18, tzinfo=TIME_ZONE),
        ),
        (
            False,
            "https://github.com/nonebot/nonebot2/actions/runs/14156878703",
            datetime(2020, 10, 5, 12, 0, 18, tzinfo=TIME_ZONE),
        ),
        (
            True,
            "https://github.com/nonebot/nonebot2/actions/runs/14156878704",
            datetime(2020, 10, 6, 12, 0, 18, tzinfo=TIME_ZONE),
        ),
        (
            False,
            "https://github.com/nonebot/nonebot2/actions/runs/14156878705",
            datetime(2020, 10, 7, 12, 0, 18, tzinfo=TIME_ZONE),
        ),
        (
            True,
            "https://github.com/nonebot/nonebot2/actions/runs/14156878706",
            datetime(2020, 10, 8, 12, 0, 18, tzinfo=TIME_ZONE),
        ),
        (
            False,
            "https://github.com/nonebot/nonebot2/actions/runs/14156878707",
            datetime(2020, 10, 9, 12, 0, 18, tzinfo=TIME_ZONE),
        ),
        (
            True,
            "https://github.com/nonebot/nonebot2/actions/runs/14156878708",
            datetime(2020, 10, 10, 12, 0, 18, tzinfo=TIME_ZONE),
        ),
    ]

    result = ValidationDict(
        type=PublishType.PLUGIN,
        raw_data={
            "name": "name",
            "load": True,
        },
        info=PluginPublishInfo.model_construct(**generate_plugin_data()),
    )

    comment = await render_comment(result, history=history)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Plugin: name

[![测试结果](https://img.shields.io/badge/RESULT-OK-green?style=for-the-badge)](https://github.com/owner/repo/actions/runs/123456)

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>
</details>
<details>
<summary>历史测试</summary>
<pre><code><li>✅ <a href=https://github.com/owner/repo/actions/runs/123456>2023-08-23 09:22:14 CST</a></li><li>✅ <a href=https://github.com/nonebot/nonebot2/actions/runs/14156878708>2020-10-10 12:00:18 CST</a></li><li>⚠️ <a href=https://github.com/nonebot/nonebot2/actions/runs/14156878707>2020-10-09 12:00:18 CST</a></li><li>✅ <a href=https://github.com/nonebot/nonebot2/actions/runs/14156878706>2020-10-08 12:00:18 CST</a></li><li>⚠️ <a href=https://github.com/nonebot/nonebot2/actions/runs/14156878705>2020-10-07 12:00:18 CST</a></li><li>✅ <a href=https://github.com/nonebot/nonebot2/actions/runs/14156878704>2020-10-06 12:00:18 CST</a></li><li>⚠️ <a href=https://github.com/nonebot/nonebot2/actions/runs/14156878703>2020-10-05 12:00:18 CST</a></li><li>✅ <a href=https://github.com/nonebot/nonebot2/actions/runs/14156878702>2020-10-04 12:00:18 CST</a></li><li>✅ <a href=https://github.com/nonebot/nonebot2/actions/runs/14156878701>2020-10-03 12:00:18 CST</a></li><li>⚠️ <a href=https://github.com/nonebot/nonebot2/actions/runs/14156878700>2020-10-02 12:00:18 CST</a></li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )
