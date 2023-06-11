import json
from collections import OrderedDict

import pytest
import respx
from nonebot.plugin import PluginMetadata
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.publish.utils import (
    generate_issue_body_plugin,
    generate_issue_body_plugin_skip_test,
)


async def test_plugin_from_issue(mocker: MockerFixture, mocked_api: MockRouter) -> None:
    """测试从 issue 中构造 PluginPublishInfo 的情况"""
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import PluginPublishInfo

    mocker.patch.object(plugin_config, "plugin_test_result", True)
    mocker.patch.object(
        plugin_config,
        "plugin_test_metadata",
        PluginMetadata(
            name="name",
            description="desc",
            usage="usage",
            homepage="https://nonebot.dev",
            type="application",
        ),
    )

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_plugin()
    mock_issue.user.login = "author"

    info = PluginPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict(exclude={"plugin_test_result"})) == OrderedDict(
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

    info.update_file()

    with plugin_config.input_config.plugin_path.open("r") as f:
        data = json.load(f)[1]
        assert data == info.dict(exclude={"plugin_test_result"})

    assert mocked_api["homepage"].called
    assert mocked_api["project_link"].called


async def test_plugin_from_issue_skip_plugin_test(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试跳过插件测试

    插件测试结果与插件元数据为空的情况
    """
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import PluginPublishInfo

    mocker.patch.object(plugin_config, "skip_plugin_test", True)
    mocker.patch.object(plugin_config, "plugin_test_result", "")

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_plugin_skip_test()
    mock_issue.user.login = "author"

    info = PluginPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict(exclude={"plugin_test_result"})) == OrderedDict(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
        type="application",
        supported_adapters=["nonebot.adapters.onebot.v11"],
    )

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_plugin_from_issue_trailing_whitespace(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试末尾如果有空格的情况"""
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import PluginPublishInfo

    mocker.patch.object(plugin_config, "plugin_test_result", True)
    mocker.patch.object(
        plugin_config,
        "plugin_test_metadata",
        PluginMetadata(
            name="name",
            description="desc",
            usage="usage",
            homepage="https://nonebot.dev",
            type="application",
        ),
    )

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_plugin(
        module_name="module_name ",
        project_link="project_link ",
    )
    mock_issue.user.login = "author"

    info = PluginPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict(exclude={"plugin_test_result"})) == OrderedDict(
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

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_plugin_info_validation_success(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试验证成功的情况"""
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import PluginPublishInfo

    mocker.patch.object(
        plugin_config,
        "plugin_test_metadata",
        PluginMetadata(
            name="name",
            description="desc",
            usage="usage",
            homepage="https://nonebot.dev",
            type="application",
        ),
    )

    info = PluginPublishInfo(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://nonebot.dev",
        tags=json.dumps([{"label": "test", "color": "#ffffff"}]),  # type: ignore
        is_official=False,
        plugin_test_result="True",  # type: ignore
        type="application",
        supported_adapters=None,
    )

    assert (
        info.validation_message
        == """> Plugin: name\n\n**✅ 所有测试通过，一切准备就绪！**\n\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 包 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li><li>✅ 插件类型: application。</li><li>✅ 插件支持的适配器: 所有。</li></code></pre></details>"""
    )

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_plugin_info_validation_failed(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试验证失败的情况"""
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import MyValidationError, PluginPublishInfo

    mocker.patch.object(plugin_config, "plugin_test_result", False)
    mocker.patch.object(plugin_config, "plugin_test_output", "test output")

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_plugin(
        project_link="project_link_failed",
        tags=[
            {"label": "test", "color": "#ffffff"},
            {"label": "testtoolong", "color": "#fffffff"},
        ],
    )
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        PluginPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Plugin: project_link_failed\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 无法获取到插件元数据。<dt>请确保插件正常加载。</dt></li><li>⚠️ 包 <a href="https://pypi.org/project/project_link_failed/">project_link_failed</a> 未发布至 PyPI。<dt>请将您的包发布至 PyPI。</dt></li><li>⚠️ 第 2 个标签名称过长<dt>请确保标签名称不超过 10 个字符。</dt></li><li>⚠️ 第 2 个标签颜色错误<dt>请确保标签颜色符合十六进制颜色码规则。</dt></li><li>⚠️ 插件加载测试未通过。<details><summary>测试输出</summary>test output</details></li></code></pre>"""
    )

    assert mocked_api["project_link_failed"].called


async def test_plugin_info_validation_partial_failed(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试验证一部分失败的情况

    插件测试失败，且没有获取到插件元数据
    """
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import MyValidationError, PluginPublishInfo

    mocker.patch.object(plugin_config, "plugin_test_result", False)
    mocker.patch.object(plugin_config, "plugin_test_output", "test output")

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_plugin()
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        PluginPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Plugin: project_link\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 无法获取到插件元数据。<dt>请确保插件正常加载。</dt></li><li>⚠️ 插件加载测试未通过。<details><summary>测试输出</summary>test output</details></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 包 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li></code></pre></details>"""
    )

    assert mocked_api["project_link"].called


async def test_plugin_info_skip_plugin_test(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试跳过插件测试的情况

    此时 plugin_test 相关的输入都是默认值
    """
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import MyValidationError, PluginPublishInfo

    mocker.patch.object(plugin_config, "skip_plugin_test", True)

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_plugin_skip_test(
        homepage="https://www.baidu.com",
    )
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        PluginPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Plugin: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保您的项目主页可访问。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 包 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 已跳过。</li><li>✅ 插件类型: application。</li><li>✅ 插件支持的适配器: nonebot.adapters.onebot.v11。</li></code></pre></details>"""
    )

    assert mocked_api["project_link"].called
    assert mocked_api["homepage_failed"].called


async def test_plugin_info_validation_failed_http_exception(
    mocker: MockerFixture,
    mocked_api: MockRouter,
) -> None:
    """测试验证失败的情况，HTTP 请求报错"""
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import MyValidationError, PluginPublishInfo

    mocker.patch.object(plugin_config, "plugin_test_result", False)
    mocker.patch.object(plugin_config, "plugin_test_output", "test output")
    mocker.patch.object(
        plugin_config,
        "plugin_test_metadata",
        PluginMetadata(
            name="name",
            description="desc",
            usage="usage",
            homepage="exception",
            type="application",
        ),
    )

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_plugin()
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        PluginPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Plugin: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 项目 <a href="exception">主页</a> 返回状态码 None。<dt>请确保您的项目主页可访问。</dt></li><li>⚠️ 插件加载测试未通过。<details><summary>测试输出</summary>test output</details></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 包 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 插件类型: application。</li><li>✅ 插件支持的适配器: 所有。</li></code></pre></details>"""
    )

    assert mocked_api["project_link"].called
    assert mocked_api["exception"].called


async def test_plugin_info_validation_adapter_not_in_store(
    mocker: MockerFixture,
    mocked_api: MockRouter,
) -> None:
    """测试验证失败的情况

    适配器未在商店里
    """
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import MyValidationError, PluginPublishInfo

    mocker.patch.object(plugin_config, "plugin_test_result", True)
    mocker.patch.object(
        plugin_config,
        "plugin_test_metadata",
        PluginMetadata(
            name="name",
            description="desc",
            usage="usage",
            homepage="https://nonebot.dev",
            type="application",
            supported_adapters={"unknown", "~onebot.v11"},
        ),
    )

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_plugin()
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        PluginPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Plugin: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 适配器 unknown 不存在。<dt>请确保适配器模块名称正确。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 包 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li><li>✅ 插件类型: application。</li></code></pre></details>"""
    )

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_plugin_info_validation_adapter_invalid(
    mocker: MockerFixture,
    mocked_api: MockRouter,
) -> None:
    """测试验证失败的情况

    适配器格式错误，手动输入的时候可能会出现
    """
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import MyValidationError, PluginPublishInfo

    mocker.patch.object(plugin_config, "skip_plugin_test", True)

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_plugin_skip_test()[:-2]
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        PluginPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Plugin: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 插件支持的适配器解码失败。<dt>请确保适配器列表为 JSON 格式。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 包 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 已跳过。</li><li>✅ 插件类型: application。</li></code></pre></details>"""
    )

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_plugin_info_validation_type_invalid(
    mocker: MockerFixture,
    mocked_api: MockRouter,
) -> None:
    """测试验证失败的情况

    插件类型错误
    """
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import MyValidationError, PluginPublishInfo

    mocker.patch.object(plugin_config, "plugin_test_result", True)
    mocker.patch.object(
        plugin_config,
        "plugin_test_metadata",
        PluginMetadata(
            name="name",
            description="desc",
            usage="usage",
            homepage="https://nonebot.dev",
            type="app",
            supported_adapters={"~onebot.v11"},
        ),
    )

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_plugin()
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        PluginPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Plugin: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 插件类型 app 不符合规范。<dt>请确保插件类型正确，当前仅支持 application 与 library。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 包 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li><li>✅ 插件支持的适配器: nonebot.adapters.onebot.v11。</li></code></pre></details>"""
    )

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_plugin_info_validation_missing_metadata(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试验证失败的情况

    插件测试成功，但缺少插件元数据
    """
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import MyValidationError, PluginPublishInfo

    mocker.patch.object(plugin_config, "plugin_test_result", True)

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_plugin()
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        PluginPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Plugin: project_link\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 无法获取到插件元数据。<dt>请填写插件元数据。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 包 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li><li>✅ 插件 <a href="https://github.com/owner/repo/actions/runs/123456">加载测试</a> 通过。</li></code></pre></details>"""
    )

    assert mocked_api["project_link"].called
