from collections import OrderedDict

from respx import MockRouter

from tests.utils.validation.utils import generate_bot_data


async def test_bot_info_validation_success(mocked_api: MockRouter) -> None:
    """测试验证成功的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_bot_data()

    result = validate_info(PublishType.BOT, data)

    assert result.is_valid
    assert OrderedDict(result.dumps_registry()) == OrderedDict(
        name="name",
        desc="desc",
        author="author",
        homepage="https://nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )

    assert mocked_api["homepage"].called


async def test_bot_info_validation_failed(mocked_api: MockRouter) -> None:
    """测试验证失败的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_bot_data(
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


async def test_bot_info_validation_failed_json_error(mocked_api: MockRouter) -> None:
    """测试验证失败的情况，JSON 解析错误"""
    from src.utils.validation import PublishType, validate_info

    data = generate_bot_data(tags="not a json")

    result = validate_info(PublishType.BOT, data)

    assert "tags" not in result.data
    assert result.errors
    assert "标签解码失败。请确保标签为 JSON 格式。" in str(result.errors)

    assert mocked_api["homepage"].called


async def test_bot_info_validation_failed_tag_field_missing(
    mocked_api: MockRouter,
) -> None:
    """测试验证失败的情况，tag 字段缺失"""
    from src.utils.validation import PublishType, validate_info

    data = generate_bot_data(
        tags=[{"label": "test"}, {"label": "test", "color": "#ffffff"}]
    )

    result = validate_info(PublishType.BOT, data)

    assert "tags" not in result.data
    assert result.errors

    assert mocked_api["homepage"].called


async def test_bot_info_validation_failed_name_tags_missing(
    mocked_api: MockRouter,
) -> None:
    """测试验证失败的情况，name, tags 字段缺失"""
    from src.utils.validation import PublishType, validate_info

    data = generate_bot_data(name=None, tags=None)

    result = validate_info(PublishType.BOT, data)

    assert "name" not in result.data
    assert "tags" not in result.data
    assert result.errors

    assert mocked_api["homepage"].called


async def test_bot_info_validation_failed_http_exception(
    mocked_api: MockRouter,
) -> None:
    """测试验证失败的情况，HTTP 请求报错"""
    from src.utils.validation import PublishType, validate_info

    data = generate_bot_data(homepage="exception")

    result = validate_info(PublishType.BOT, data)

    assert "homepage" not in result.data
    assert result.errors

    assert mocked_api["exception"].called
