from collections import OrderedDict

from respx import MockRouter

from tests.utils.validation.utils import generate_plugin_data


async def test_plugin_info_validation_success(mocked_api: MockRouter) -> None:
    """测试验证成功的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data()

    result = validate_info(PublishType.PLUGIN, data)

    assert result["data"]
    assert OrderedDict(result["data"]) == OrderedDict(
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
    assert not result["errors"]
    assert result["type"] == PublishType.PLUGIN
    assert result["name"] == "name"
    assert result["author"] == "author"

    assert mocked_api["homepage"].called


async def test_plugin_info_validation_failed(mocked_api: MockRouter) -> None:
    """测试验证失败的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_plugin_data(
        homepage="https://www.baidu.com",
        tags=[
            {"label": "test", "color": "#ffffff"},
            {"label": "testtoolong", "color": "#fffffff"},
        ],
        previous_data=[],
        type="invalid",
        supported_adapters=["missing", "~onebot.v11"],
    )

    result = validate_info(PublishType.PLUGIN, data)

    assert result == {
        "valid": False,
        "data": {
            "module_name": "module_name",
            "project_link": "project_link",
            "name": "name",
            "desc": "desc",
            "author": "author",
        },
        "errors": [
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
                "url": "https://errors.pydantic.dev/2.7/v/string_too_long",
            },
            {
                "type": "color_error",
                "loc": ("tags", 1, "color"),
                "msg": "颜色格式不正确",
                "input": "#fffffff",
            },
            {
                "type": "plugin.type",
                "loc": ("type",),
                "msg": "插件类型不符合规范",
                "input": "invalid",
            },
            {
                "type": "supported_adapters.missing",
                "loc": ("supported_adapters",),
                "msg": "适配器 missing 不存在",
                "input": ["missing", "~onebot.v11"],
                "ctx": {
                    "missing_adapters": ["missing"],
                    "missing_adapters_str": "missing",
                },
            },
        ],
        "type": PublishType.PLUGIN,
        "name": "name",
        "author": "author",
    }

    assert mocked_api["homepage_failed"].called
