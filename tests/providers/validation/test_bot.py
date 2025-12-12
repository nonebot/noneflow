from inline_snapshot import snapshot
from respx import MockRouter

from tests.providers.validation.utils import generate_bot_data


async def test_bot_info_validation_success(mocked_api: MockRouter) -> None:
    """测试验证成功的情况"""
    from src.providers.validation import BotPublishInfo, PublishType, validate_info

    data = generate_bot_data()

    result = validate_info(PublishType.BOT, data, [])

    assert result.valid
    assert result.type == PublishType.BOT
    assert result.raw_data == snapshot(
        {
            "name": "name",
            "desc": "desc",
            "author": "author",
            "homepage": "https://nonebot.dev",
            "tags": '[{"label": "test", "color": "#ffffff"}]',
            "author_id": 1,
        }
    )
    assert isinstance(result.info, BotPublishInfo)
    assert result.errors == []

    assert mocked_api["homepage"].called


async def test_bot_info_validation_failed(mocked_api: MockRouter) -> None:
    """测试验证失败的情况"""
    from src.providers.validation import PublishType, ValidationDict, validate_info

    data = generate_bot_data(
        name="tooooooooooooooooooooooooooooooooooooooooooooooooog",
        homepage="https://www.baidu.com",
        tags=[
            {"label": "test", "color": "#ffffff"},
            {"label": "testtoolong", "color": "#fffffff"},
        ],
    )

    result = validate_info(PublishType.BOT, data, [])

    assert result == snapshot(
        ValidationDict(
            errors=[
                {
                    "type": "string_too_long",
                    "loc": ("name",),
                    "msg": "字符串长度不能超过 50 个字符",
                    "input": "tooooooooooooooooooooooooooooooooooooooooooooooooog",
                    "ctx": {"max_length": 50},
                    "url": "https://errors.pydantic.dev/2.12/v/string_too_long",
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
                    "url": "https://errors.pydantic.dev/2.12/v/string_too_long",
                },
                {
                    "type": "color_error",
                    "loc": ("tags", 1, "color"),
                    "msg": "颜色格式不正确",
                    "input": "#fffffff",
                },
            ],
            raw_data={
                "name": "tooooooooooooooooooooooooooooooooooooooooooooooooog",
                "desc": "desc",
                "author": "author",
                "homepage": "https://www.baidu.com",
                "tags": '[{"label": "test", "color": "#ffffff"}, {"label": "testtoolong", "color": "#fffffff"}]',
                "author_id": 1,
            },
            type=PublishType.BOT,
            valid_data={"desc": "desc", "author": "author", "author_id": 1},
        )
    )

    assert mocked_api["homepage_failed"].called


async def test_bot_name_duplication(mocked_api: MockRouter) -> None:
    """测试机器人名称重复的情况"""
    from src.providers.validation import PublishType, ValidationDict, validate_info

    data = generate_bot_data()
    previous_data = [
        {
            "name": "name",
            "homepage": "https://nonebot.dev",
        }
    ]

    result = validate_info(PublishType.BOT, data, previous_data)

    assert result == snapshot(
        ValidationDict(
            errors=[
                {
                    "type": "duplication",
                    "loc": (),
                    "msg": "名称 name 加主页 https://nonebot.dev 的值与商店重复",
                    "input": {
                        "name": "name",
                        "desc": "desc",
                        "author": "author",
                        "homepage": "https://nonebot.dev",
                        "tags": '[{"label": "test", "color": "#ffffff"}]',
                        "author_id": 1,
                    },
                    "ctx": {"name": "name", "homepage": "https://nonebot.dev"},
                }
            ],
            raw_data={
                "name": "name",
                "desc": "desc",
                "author": "author",
                "homepage": "https://nonebot.dev",
                "tags": '[{"label": "test", "color": "#ffffff"}]',
                "author_id": 1,
            },
            type=PublishType.BOT,
        )
    )

    assert not mocked_api["homepage"].called


async def test_bot_previos_data_missing(mocked_api: MockRouter) -> None:
    """测试机器人名称重复的情况"""
    from src.providers.validation import PublishType, ValidationDict, validate_info

    data = generate_bot_data()

    result = validate_info(PublishType.BOT, data, None)

    assert result == snapshot(
        ValidationDict(
            errors=[
                {
                    "type": "previous_data",
                    "loc": (),
                    "msg": "未获取到数据列表",
                    "input": {
                        "name": "name",
                        "desc": "desc",
                        "author": "author",
                        "homepage": "https://nonebot.dev",
                        "tags": '[{"label": "test", "color": "#ffffff"}]',
                        "author_id": 1,
                    },
                }
            ],
            raw_data={
                "name": "name",
                "desc": "desc",
                "author": "author",
                "homepage": "https://nonebot.dev",
                "tags": '[{"label": "test", "color": "#ffffff"}]',
                "author_id": 1,
            },
            type=PublishType.BOT,
        )
    )

    assert not mocked_api["homepage"].called
