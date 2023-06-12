import json
from collections import OrderedDict

import pytest
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.publish.utils import generate_issue_body_adapter


async def test_adapter_from_issue(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试从 issue 中构造 AdapterPublishInfo 的情况"""
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import AdapterPublishInfo

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_adapter()
    mock_issue.user.login = "author"

    info = AdapterPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict()) == OrderedDict(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )

    info.update_file()

    with plugin_config.input_config.adapter_path.open("r") as f:
        data = json.load(f)[1]
        assert data == info.dict()

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_from_issue_trailing_whitespace(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试末尾如果有空格的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_adapter(
        name="name ",
        desc="desc ",
        module_name="module_name ",
        project_link="project_link ",
        homepage="https://nonebot.dev ",
    )
    mock_issue.user.login = "author"

    info = AdapterPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict()) == OrderedDict(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_info_validation_success(mocked_api: MockRouter) -> None:
    """测试验证成功的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo

    info = AdapterPublishInfo(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://nonebot.dev",
        tags=json.dumps([{"label": "test", "color": "#ffffff"}]),  # type: ignore
        is_official=False,
    )

    assert (
        info.validation_message
        == """> Adapter: name\n\n**✅ 所有测试通过，一切准备就绪！**\n\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 包 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li></code></pre></details>"""
    )

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_adapter_info_validation_failed(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试验证失败的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo, MyValidationError

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_adapter(
        project_link="project_link_failed",
        homepage="https://www.baidu.com",
        tags=[{"label": "test", "color": "#fffffff"}],
    )
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        AdapterPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Adapter: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 包 <a href="https://pypi.org/project/project_link_failed/">project_link_failed</a> 未发布至 PyPI。<dt>请将您的包发布至 PyPI。</dt></li><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保您的项目主页可访问。</dt></li><li>⚠️ 第 1 个标签颜色错误<dt>请确保标签颜色符合十六进制颜色码规则。</dt></li></code></pre>"""
    )

    assert mocked_api["project_link_failed"].called
    assert mocked_api["homepage_failed"].called


async def test_adapter_info_validation_partial_failed(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试验证一部分失败的情况"""
    from src.plugins.publish.validation import AdapterPublishInfo, MyValidationError

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_adapter(
        homepage="https://www.baidu.com",
    )
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        AdapterPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Adapter: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保您的项目主页可访问。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 包 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li></code></pre></details>"""
    )

    assert mocked_api["project_link"].called
    assert mocked_api["homepage_failed"].called


async def test_adapter_info_name_validation_failed(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试名称不符合规范的情况

    名称过长
    重复的项目名与报名
    """
    from src.plugins.publish.validation import AdapterPublishInfo, MyValidationError

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_adapter(
        name="looooooooooooooooooooooooooooooooooooooooooooooooooooooooong",
        module_name="module_name1",
        project_link="project_link1",
    )
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        AdapterPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Adapter: looooooooooooooooooooooooooooooooooooooooooooooooooooooooong\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 名称过长。<dt>请确保名称不超过 50 个字符。</dt></li><li>⚠️ PyPI 项目名 project_link1 加包名 module_name1 的值与商店重复。<dt>请确保没有重复发布。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li><li>✅ 包 <a href="https://pypi.org/project/project_link1/">project_link1</a> 已发布至 PyPI。</li></code></pre></details>"""
    )

    assert mocked_api["project_link1"].called
    assert mocked_api["homepage"].called


async def test_adapter_info_validation_failed_http_exception(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试验证失败的情况，HTTP 请求报错"""
    from src.plugins.publish.validation import AdapterPublishInfo, MyValidationError

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_adapter(homepage="exception")
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        AdapterPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Adapter: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 项目 <a href="exception">主页</a> 返回状态码 None。<dt>请确保您的项目主页可访问。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 包 <a href="https://pypi.org/project/project_link/">project_link</a> 已发布至 PyPI。</li></code></pre></details>"""
    )

    assert mocked_api["project_link"].called
    assert mocked_api["exception"].called
