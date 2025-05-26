from inline_snapshot import snapshot
from nonebug import App


async def test_history_workflow(app: App, mock_datetime):
    from src.plugins.github.plugins.publish.utils import (
        get_history_workflow_from_comment,
    )
    from src.providers.constants import TIME_ZONE


    CONTENT = """
# 📃 商店发布检查结果

> Plugin: nonebot-plugin-emojilike-automonkey

**✅ 所有测试通过，一切准备就绪！**


<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://github.com/2580m/nonebot-plugin-emojilike-automonkey">主页</a> 返回状态码 200。</li><li>✅ 项目 <a href="https://pypi.org/project/nonebot-plugin-emojilike-automonkey/">nonebot-plugin-emojilike-automonkey</a> 已发布至 PyPI。</li><li>✅ 标签: emoji-#6677ff。</li><li>✅ 插件类型: application。</li><li>✅ 插件支持的适配器: nonebot.adapters.onebot.v11。</li><li>✅ 插件 <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">加载测试</a> 通过。</li><li>✅ 版本号: 0.0.12。</li><li>✅ 发布时间：2025-03-28 02:03:18 CST。</li></code></pre>
</details>

<details>
<summary>历史测试</summary>
<pre><code>
<li>⚠️ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:21:18 CST</a>。</li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:21:18 CST</a>。</li><li>✅ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:22:18 CST</a>。</li><li>⚠️ <a href="https://github.com/nonebot/nonebot2/actions/runs/14156878699">2025-03-28 02:22:18 CST</a>。</li>
</code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后勾选插件测试勾选框重新运行插件测试。

♻️ 评论已更新至最新检查结果

💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    history = [
        (valid, url, time.astimezone(TIME_ZONE).strftime("%Y-%m-%d %H:%M:%S %Z"))
        for valid, url, time in await get_history_workflow_from_comment(CONTENT)
    ]
    assert history == snapshot(
        [
            (
                False,
                "https://github.com/nonebot/nonebot2/actions/runs/14156878699",
                "2025-03-28 02:21:18 CST",
            ),
            (
                True,
                "https://github.com/nonebot/nonebot2/actions/runs/14156878699",
                "2025-03-28 02:21:18 CST",
            ),
            (
                True,
                "https://github.com/nonebot/nonebot2/actions/runs/14156878699",
                "2025-03-28 02:22:18 CST",
            ),
            (
                False,
                "https://github.com/nonebot/nonebot2/actions/runs/14156878699",
                "2025-03-28 02:22:18 CST",
            ),
        ]
    )
