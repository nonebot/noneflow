import json
from collections import OrderedDict

import pytest
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.publish.utils import generate_issue_body_bot


async def test_bot_from_issue(mocker: MockerFixture, mocked_api: MockRouter) -> None:
    """测试从 issue 中构造 BotPublishInfo"""
    from src.plugins.publish.config import plugin_config
    from src.plugins.publish.validation import BotPublishInfo

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_bot()
    mock_issue.user.login = "author"

    info = BotPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict()) == OrderedDict(
        name="name",
        desc="desc",
        author="author",
        homepage="https://nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )

    info.update_file()

    with plugin_config.input_config.bot_path.open("r") as f:
        data = json.load(f)[1]
        assert data == info.dict()

    assert mocked_api["homepage"].called


async def test_bot_from_issue_trailing_whitespace(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试末尾如果有空格的情况"""
    from src.plugins.publish.validation import BotPublishInfo

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_bot(
        name="name ",
        desc="desc ",
        homepage="https://nonebot.dev ",
    )
    mock_issue.user.login = "author"

    info = BotPublishInfo.from_issue(mock_issue)

    assert OrderedDict(info.dict()) == OrderedDict(
        name="name",
        desc="desc",
        author="author",
        homepage="https://nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )

    assert mocked_api["homepage"].called


async def test_bot_info_validation_success(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试验证成功的情况"""
    from src.plugins.publish.validation import BotPublishInfo

    info = BotPublishInfo(
        name="name",
        desc="desc",
        author="author",
        homepage="https://nonebot.dev",
        tags=json.dumps([{"label": "test", "color": "#ffffff"}]),  # type: ignore
        is_official=False,
    )

    assert (
        info.validation_message
        == """> Bot: name\n\n**✅ 所有测试通过，一切准备就绪！**\n\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li></code></pre></details>"""
    )

    assert mocked_api["homepage"].called


async def test_bot_info_validation_failed(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试验证失败的情况"""
    from src.plugins.publish.validation import BotPublishInfo, MyValidationError

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_bot(
        homepage="https://www.baidu.com",
        tags=[
            {"label": "test", "color": "#ffffff"},
            {"label": "testtoolong", "color": "#fffffff"},
        ],
    )
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        BotPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Bot: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保您的项目主页可访问。</dt></li><li>⚠️ 第 2 个标签名称过长<dt>请确保标签名称不超过 10 个字符。</dt></li><li>⚠️ 第 2 个标签颜色错误<dt>请确保标签颜色符合十六进制颜色码规则。</dt></li></code></pre>"""
    )

    assert mocked_api["homepage_failed"].called


async def test_bot_info_validation_failed_json_error(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试验证失败的情况，JSON 解析错误"""
    from src.plugins.publish.validation import BotPublishInfo, MyValidationError

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_bot(
        homepage="https://www.baidu.com",
        tags="not a json",
    )
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        BotPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Bot: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保您的项目主页可访问。</dt></li><li>⚠️ 标签解码失败。<dt>请确保标签为 JSON 格式。</dt></li></code></pre>"""
    )

    assert mocked_api["homepage_failed"].called


async def test_bot_info_validation_failed_tag_field_missing(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试验证失败的情况，tag 字段缺失"""
    from src.plugins.publish.validation import BotPublishInfo, MyValidationError

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_bot(
        homepage="https://www.baidu.com",
        tags=[{"label": "test"}],
    )
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        BotPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Bot: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 项目 <a href="https://www.baidu.com">主页</a> 返回状态码 404。<dt>请确保您的项目主页可访问。</dt></li><li>⚠️ 第 1 个标签缺少 color 字段。<dt>请确保标签字段完整。</dt></li></code></pre>"""
    )

    assert mocked_api["homepage_failed"].called


async def test_bot_info_validation_failed_name_tags_missing(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试验证失败的情况，name, tags 字段缺失"""
    from src.plugins.publish.validation import BotPublishInfo, MyValidationError

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_bot(name="", tags="")
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        BotPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Bot: \n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 名称: 无法匹配到数据。<dt>请确保填写该项目。</dt></li><li>⚠️ 标签: 无法匹配到数据。<dt>请确保填写该项目。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 项目 <a href="https://nonebot.dev">主页</a> 返回状态码 200。</li></code></pre></details>"""
    )

    assert mocked_api["homepage"].called


async def test_bot_info_validation_failed_http_exception(
    mocker: MockerFixture, mocked_api: MockRouter
) -> None:
    """测试验证失败的情况，HTTP 请求报错"""
    from src.plugins.publish.validation import BotPublishInfo, MyValidationError

    mock_issue = mocker.MagicMock()
    mock_issue.body = generate_issue_body_bot(homepage="exception")
    mock_issue.user.login = "author"

    with pytest.raises(MyValidationError) as e:
        BotPublishInfo.from_issue(mock_issue)

    assert (
        e.value.message
        == """> Bot: name\n\n**⚠️ 在发布检查过程中，我们发现以下问题：**\n<pre><code><li>⚠️ 项目 <a href="exception">主页</a> 返回状态码 None。<dt>请确保您的项目主页可访问。</dt></li></code></pre>\n<details><summary>详情</summary><pre><code><li>✅ 标签: test-#ffffff。</li></code></pre></details>"""
    )

    assert mocked_api["exception"].called
