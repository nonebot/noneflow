from collections import OrderedDict

from respx import MockRouter

from tests.utils.validation.utils import generate_plugin_data


async def test_plugin_info_validation_success(mocked_api: MockRouter) -> None:
    """测试验证成功的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data()

    result = validate_info(PublishType.PLUGIN, data)

    assert result.is_valid
    assert OrderedDict(result.dumps_registry()) == OrderedDict(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
        type="application",
        supported_adapters=None,
    )

    assert mocked_api["homepage"].called
    comment = await result.render_issue_comment()
    assert (
        comment
        == """# 📃 商店发布检查结果\n\n> Plugin: name\n\n✅ 所有测试通过，一切准备就绪！\n\n\n<details>\n<summary>详情</summary>\n<pre><code><li>✅ 项目 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 标签: test-#ffffff。</li><li>✅ 插件类型: application。</li><li>✅ 插件支持的适配器: 所有。</li><li>✅ 插件 <a href="https://github.com/github/actions/runs/123456">加载测试</a> 通过。</li></code></pre>\n</details>\n\n---\n\n💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。\n\n\n💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)\n<!-- NONEFLOW -->"""
    )

    registry = await result.render_registry_message()
    assert (
        registry
        == """✅ 所有测试通过，一切准备就绪！\n\n<details>\n  <summary>详情</summary>\n  <pre><code><li>✅ 项目 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 标签: test-#ffffff。</li><li>✅ 插件类型: application。</li><li>✅ 插件支持的适配器: 所有。</li><li>✅ 插件 <a href="https://github.com/github/actions/runs/123456">加载测试</a> 通过。</li></code></pre>\n</details>\n"""
    )


async def test_bot_info_validation_failed(mocked_api: MockRouter) -> None:
    """测试验证失败的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(
        homepage="https://www.baidu.com",
        tags=[
            {"label": "test", "color": "#ffffff"},
            {"label": "testtoolong", "color": "#fffffff"},
        ],
    )

    result = validate_info(PublishType.BOT, data)

    assert not result.is_valid
    assert "homepage" not in result.data
    assert "tags" not in result.data
    assert result.errors

    assert mocked_api["homepage_failed"].called
