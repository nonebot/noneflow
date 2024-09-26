from collections import OrderedDict

from respx import MockRouter

from tests.utils.validation.utils import generate_bot_data


async def test_bot_info_validation_success(mocked_api: MockRouter) -> None:
    """测试验证成功的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_bot_data()

    result = validate_info(PublishType.BOT, data)

    assert result["valid"]
    assert OrderedDict(result["data"]) == OrderedDict(
        name="name",
        desc="desc",
        author="author",
        homepage="https://nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )
    assert not result["errors"]
    assert result["type"] == PublishType.BOT
    assert result["name"] == "name"
    assert result["author"] == "author"

    assert mocked_api["homepage"].called


async def test_bot_info_validation_failed(mocked_api: MockRouter) -> None:
    """测试验证失败的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_bot_data(
        name="tooooooooooooooooooooooooooooooooooooooooooooooooog",
        homepage="https://www.baidu.com",
        tags=[
            {"label": "test", "color": "#ffffff"},
            {"label": "testtoolong", "color": "#fffffff"},
        ],
    )

    result = validate_info(PublishType.BOT, data)

    assert result == {
        "valid": False,
        "data": {"desc": "desc", "author": "author"},
        "errors": [
            {
                "type": "string_too_long",
                "loc": ("name",),
                "msg": "字符串长度不能超过 50 个字符",
                "input": "tooooooooooooooooooooooooooooooooooooooooooooooooog",
                "ctx": {"max_length": 50},
                "url": "https://errors.pydantic.dev/2.8/v/string_too_long",
            },
            {
                "type": "homepage",
                "loc": ("homepage",),
                "msg": "项目主页无法访问",
                "input": "https://www.baidu.com",
                "ctx": {"status_code": 404, "msg": ""},
            },
            {
                "type": "string_too_long",
                "loc": ("tags", 1, "label"),
                "msg": "字符串长度不能超过 10 个字符",
                "input": "testtoolong",
                "ctx": {"max_length": 10},
                "url": "https://errors.pydantic.dev/2.8/v/string_too_long",
            },
            {
                "type": "color_error",
                "loc": ("tags", 1, "color"),
                "msg": "颜色格式不正确",
                "input": "#fffffff",
            },
        ],
        "type": PublishType.BOT,
        "name": "tooooooooooooooooooooooooooooooooooooooooooooooooog",
        "author": "author",
    }

    assert mocked_api["homepage_failed"].called
