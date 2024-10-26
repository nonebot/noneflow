from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockFixture


async def test_render_error_bot(app: App):
    """机器人数据"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import PublishType, ValidationDict

    result = ValidationDict(
        type=PublishType.BOT,
        raw_data={"name": "CoolQBot"},
        context={
            "valid_data": {
                "desc": "基于 NoneBot2 的聊天机器人",
                "author": "he0119",
                "is_official": False,
            }
        },
        errors=[
            {
                "loc": ("name",),
                "msg": "名称不能超过 50 个字符。",
                "type": "string_too_long",
                "input": "tooooooooooooooooooooooooooooooooooooooooooooooooog",
                "ctx": {"max_length": 50},
            },
            {
                "loc": ("homepage",),
                "msg": "项目主页不可访问。",
                "type": "homepage",
                "ctx": {"status_code": 404},
                "input": "https://www.baidu.com",
            },
            {
                "loc": ("tags", 1, "label"),
                "msg": "标签名称超过 10 个字符。",
                "type": "string_too_long",
                "input": "testtoolong",
                "ctx": {"max_length": 10},
            },
            {
                "loc": ("tags", 1, "color"),
                "msg": "标签颜色不符合十六进制颜色码规则。",
                "type": "color_error",
                "input": "#fffffff",
            },
        ],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Bot: CoolQBot

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 名称: 字符过多。<dt>请确保其不超过 50 个字符。</dt></li><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保你的项目主页可访问。</dt></li><li>⚠️ 第 2 个标签名称过长。<dt>请确保标签名称不超过 10 个字符。</dt></li><li>⚠️ 第 2 个标签颜色错误。<dt>请确保标签颜色符合十六进制颜色码规则。</dt></li></code></pre>


---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )


async def test_render_error_adapter(app: App):
    """适配器数据"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import PublishType, ValidationDict

    result = ValidationDict(
        type=PublishType.ADAPTER,
        raw_data={"name": "大别野"},
        context={
            "valid_data": {
                "module_name": "nonebot.adapters.villa",
                "project_link": "nonebot-adapter-villa",
                "desc": "米游社大别野官方Bot适配",
                "author": "CMHopeSunshine",
                "author_id": 1,
                "is_official": False,
            }
        },
        errors=[
            {
                "loc": ("module_name",),
                "msg": "包名不符合规范。",
                "type": "module_name",
                "input": "module_name/",
            },
            {
                "loc": ("project_link",),
                "msg": "PyPI 项目名不存在。",
                "type": "project_link.not_found",
                "input": "project_link_failed",
            },
            {
                "loc": ("name",),
                "msg": "名称不能超过 50 个字符。",
                "type": "string_too_long",
                "input": "tooooooooooooooooooooooooooooooooooooooooooooooooog",
                "ctx": {"max_length": 50},
            },
            {
                "loc": ("homepage",),
                "msg": "项目主页不可访问。",
                "type": "homepage",
                "ctx": {"status_code": 404},
                "input": "https://www.baidu.com",
            },
            {
                "loc": ("tags", 1, "label"),
                "msg": "标签名称超过 10 个字符。",
                "type": "string_too_long",
                "input": "testtoolong",
                "ctx": {"max_length": 10},
            },
            {
                "loc": ("tags", 1, "color"),
                "msg": "标签颜色不符合十六进制颜色码规则。",
                "type": "color_error",
                "input": "#fffffff",
            },
        ],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Adapter: 大别野

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 包名 module_name/ 不符合规范。<dt>请确保包名正确。</dt></li><li>⚠️ 项目 <a href="https://pypi.org/project/project_link_failed/">project_link_failed</a> 未发布至 PyPI。<dt>请将你的项目发布至 PyPI。</dt></li><li>⚠️ 名称: 字符过多。<dt>请确保其不超过 50 个字符。</dt></li><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保你的项目主页可访问。</dt></li><li>⚠️ 第 2 个标签名称过长。<dt>请确保标签名称不超过 10 个字符。</dt></li><li>⚠️ 第 2 个标签颜色错误。<dt>请确保标签颜色符合十六进制颜色码规则。</dt></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://pypi.org/project/nonebot-adapter-villa/">nonebot-adapter-villa</a> 已发布至 PyPI。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )


async def test_render_error_plugin(app: App, mocker: MockFixture):
    """插件数据"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import PublishType, ValidationDict

    result = ValidationDict(
        type=PublishType.PLUGIN,
        raw_data={"name": "帮助"},
        context={
            "valid_data": {
                "name": "帮助",
                "desc": "获取插件帮助信息",
                "author": "he0119",
                "author_id": 1,
                "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
                "tags": [],
                "is_official": False,
                "metadata": None,
                "load": True,
            }
        },
        errors=[
            {
                "loc": (),
                "msg": "PyPI 项目名 project_link 加包名 module_name 的值与商店重复。",
                "type": "duplication",
                "ctx": {"project_link": "project_link", "module_name": "module_name"},
                "input": None,
            },
            {
                "loc": ("name",),
                "msg": "名称不能超过 50 个字符。",
                "type": "string_too_long",
                "input": "tooooooooooooooooooooooooooooooooooooooooooooooooog",
                "ctx": {"max_length": 50},
            },
            {
                "loc": ("homepage",),
                "msg": "项目主页不可访问。",
                "type": "homepage",
                "ctx": {"status_code": 404},
                "input": "https://www.baidu.com",
            },
            {
                "loc": ("tags", 1, "label"),
                "msg": "标签名称超过 10 个字符。",
                "type": "string_too_long",
                "input": "testtoolong",
                "ctx": {"max_length": 10},
            },
            {
                "loc": ("tags", 1, "color"),
                "msg": "标签颜色不符合十六进制颜色码规则。",
                "type": "color_error",
                "input": "#fffffff",
            },
            {
                "loc": ("type",),
                "msg": "field required",
                "type": "missing",
                "input": None,
            },
        ],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Plugin: 帮助

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ PyPI 项目名 project_link 加包名 module_name 的值与商店重复。<dt>请确保没有重复发布。</dt></li><li>⚠️ 名称: 字符过多。<dt>请确保其不超过 50 个字符。</dt></li><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保你的项目主页可访问。</dt></li><li>⚠️ 第 2 个标签名称过长。<dt>请确保标签名称不超过 10 个字符。</dt></li><li>⚠️ 第 2 个标签颜色错误。<dt>请确保标签颜色符合十六进制颜色码规则。</dt></li><li>⚠️ 插件类型: 无法匹配到数据。<dt>请确保填写该数据项。</dt></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://github.com/he0119/nonebot-plugin-treehelp">主页</a> 返回状态码 200。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )


async def test_render_error_plugin_load_test(app: App):
    """插件加载测试失败，并且没有获取到元数据"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import PublishType, ValidationDict

    result = ValidationDict(
        type=PublishType.PLUGIN,
        raw_data={"name": "帮助"},
        context={
            "valid_data": {
                "name": "帮助",
                "desc": "获取插件帮助信息",
                "author": "he0119",
                "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
                "tags": [],
                "is_official": False,
            }
        },
        errors=[
            {
                "loc": ("metadata",),
                "msg": "无法获取到插件元数据。",
                "type": "metadata",
                "ctx": {"load": False},
                "input": None,
            },
            {
                "loc": ("plugin.test",),
                "msg": "插件无法正常加载",
                "type": "plugin.test",
                "ctx": {"output": "output"},
                "input": None,
            },
        ],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Plugin: 帮助

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ : 无法获取到插件元数据。</li><li>⚠️ 插件加载测试未通过。<details><summary>测试输出</summary>output</details></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 项目 <a href="https://github.com/he0119/nonebot-plugin-treehelp">主页</a> 返回状态码 200。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )


async def test_render_error_plugin_metadata(app: App, mocker: MockFixture):
    """插件加载成功，但缺少元数据的情况"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import PublishType, ValidationDict

    result = ValidationDict(
        type=PublishType.PLUGIN,
        raw_data={"name": "帮助"},
        context={"valid_data": {"author": "he0119", "tags": [], "is_official": False}},
        errors=[
            {
                "loc": ("metadata",),
                "msg": "无法获取到插件元数据。",
                "type": "metadata",
                "ctx": {"load": True},
                "input": None,
            }
        ],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Plugin: 帮助

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ : 无法获取到插件元数据。</li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )


async def test_render_error_tags_invalid(app: App, mocker: MockFixture):
    """标签不合法的情况"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import PublishType, ValidationDict

    result = ValidationDict(
        type=PublishType.PLUGIN,
        raw_data={"name": "帮助"},
        context={"valid_data": {"author": "he0119", "tags": [], "is_official": False}},
        errors=[
            {
                "loc": ("tags", 2),
                "msg": "value is not a valid dict",
                "type": "model_type",
                "input": 1,
            },
            {
                "loc": ("tags",),
                "msg": "value is not a valid list",
                "type": "list_type",
                "input": '"test"',
            },
            {
                "loc": ("tags",),
                "msg": "Invalid JSON",
                "type": "json_type",
                "input": "not json",
            },
        ],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Plugin: 帮助

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 第 3 个标签格式错误。<dt>请确保标签为字典。</dt></li><li>⚠️ 标签: 格式错误。<dt>请确保其为列表。</dt></li><li>⚠️ 标签: 解码失败。<dt>请确保其为 JSON 格式。</dt></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )


async def test_render_type_error(app: App, mocker: MockFixture):
    """插件类型与适配器错误"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import PublishType, ValidationDict

    result = ValidationDict(
        type=PublishType.PLUGIN,
        raw_data={"name": "帮助"},
        context={"valid_data": {"author": "he0119", "tags": [], "is_official": False}},
        errors=[
            {
                "loc": ("type",),
                "msg": "插件类型不符合规范。",
                "type": "plugin.type",
                "input": "invalid",
            },
            {
                "loc": ("supported_adapters",),
                "msg": "适配器 missing 不存在。",
                "type": "supported_adapters.missing",
                "ctx": {"missing_adapters": {"missing"}},
                "input": ["missing", "~onebot.v11"],
            },
            {
                "loc": ("supported_adapters",),
                "msg": "value is not a valid set",
                "type": "set_type",
                "input": '"test"',
            },
        ],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Plugin: 帮助

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 插件类型 invalid 不符合规范。<dt>请确保插件类型正确，当前仅支持 application 与 library。</dt></li><li>⚠️ 适配器 missing 不存在。<dt>请确保适配器模块名称正确。</dt></li><li>⚠️ 插件支持的适配器: 格式错误。<dt>请确保其为集合。</dt></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )


async def test_render_unknown_error(app: App, mocker: MockFixture):
    """未知错误"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import PublishType, ValidationDict

    result = ValidationDict(
        type=PublishType.PLUGIN,
        raw_data={"name": "帮助"},
        context={"valid_data": {"author": "he0119", "tags": [], "is_official": False}},
        errors=[
            {
                "loc": ("tests", 2, "test"),
                "msg": "unknown error",
                "type": "type_error.unknown",
                "input": 1,
            }
        ],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Plugin: 帮助

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ : unknown error</li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )


async def test_render_http_error(app: App, mocker: MockFixture):
    """网络请求报错"""
    from src.plugins.github.plugins.publish.render import render_comment
    from src.providers.validation import PublishType, ValidationDict

    result = ValidationDict(
        type=PublishType.PLUGIN,
        raw_data={"name": "帮助"},
        context={"valid_data": {"author": "he0119", "tags": [], "is_official": False}},
        errors=[
            {
                "loc": ("homepage",),
                "msg": "项目主页不可访问。",
                "type": "homepage",
                "ctx": {"status_code": 404},
                "input": "https://www.baidu.com",
            },
            {
                "loc": ("homepage",),
                "msg": "项目主页无法访问。",
                "type": "homepage",
                "ctx": {
                    "status_code": -1,
                    "msg": "Request URL is missing an 'http://' or 'https://' protocol.",
                },
                "input": "12312",
            },
        ],
    )

    comment = await render_comment(result)
    assert comment == snapshot(
        """\
# 📃 商店发布检查结果

> Plugin: 帮助

**⚠️ 在发布检查过程中，我们发现以下问题：**

<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保你的项目主页可访问。</dt></li><li>⚠️ 项目 <a href="12312">主页</a> 访问出错。<details><summary>错误信息</summary></details></li></code></pre>

<details>
<summary>详情</summary>
<pre><code><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre>
</details>

---

💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。
💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。


💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)
<!-- NONEFLOW -->
"""
    )
