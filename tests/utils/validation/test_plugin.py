from inline_snapshot import snapshot
from respx import MockRouter

from tests.utils.validation.utils import generate_plugin_data


async def test_plugin_info_validation_success(mocked_api: MockRouter) -> None:
    """测试验证成功的情况"""
    from src.providers.validation import PluginPublishInfo, PublishType, validate_info

    data = generate_plugin_data()

    result = validate_info(PublishType.PLUGIN, data, [])

    assert result.valid
    assert result.type == PublishType.PLUGIN
    assert result.raw_data == snapshot(
        {
            "name": "name",
            "desc": "desc",
            "author": "author",
            "module_name": "module_name",
            "project_link": "project_link",
            "homepage": "https://nonebot.dev",
            "tags": '[{"label": "test", "color": "#ffffff"}]',
            "type": "application",
            "supported_adapters": None,
            "skip_test": False,
            "metadata": True,
            "author_id": 1,
            "load": True,
            "version": "0.0.1",
            "test_output": "test_output",
            "time": "2023-09-01T00:00:00+00:00Z",
        }
    )
    assert isinstance(result.info, PluginPublishInfo)
    assert result.errors == []

    assert mocked_api["homepage"].called


async def test_plugin_info_validation_failed(mocked_api: MockRouter) -> None:
    """测试验证失败的情况"""
    from src.providers.validation import PublishType, ValidationDict, validate_info

    data = generate_plugin_data(
        homepage="https://www.baidu.com",
        tags=[
            {"label": "test", "color": "#ffffff"},
            {"label": "testtoolong", "color": "#fffffff"},
        ],
        type="invalid",
        supported_adapters=["missing", "~onebot.v11"],
    )

    result = validate_info(PublishType.PLUGIN, data, [])

    assert result == snapshot(
        ValidationDict(
            errors=[
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
                    "msg": "插件类型只能是 application 或 library",
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
            info=None,
            raw_data={
                "author": "author",
                "module_name": "module_name",
                "project_link": "project_link",
                "tags": '[{"label": "test", "color": "#ffffff"}, {"label": "testtoolong", "color": "#fffffff"}]',
                "name": "name",
                "desc": "desc",
                "homepage": "https://www.baidu.com",
                "type": "invalid",
                "supported_adapters": ["missing", "~onebot.v11"],
                "skip_test": False,
                "metadata": True,
                "author_id": 1,
                "load": True,
                "version": "0.0.1",
                "test_output": "test_output",
                "time": "2023-09-01T00:00:00+00:00Z",
            },
            type=PublishType.PLUGIN,
            valid_data={
                "module_name": "module_name",
                "project_link": "project_link",
                "time": "2023-09-01T00:00:00+00:00Z",
                "name": "name",
                "desc": "desc",
                "author": "author",
                "author_id": 1,
                "load": True,
                "metadata": True,
                "skip_test": False,
                "version": "0.0.1",
                "test_output": "test_output",
            },
        )
    )

    assert mocked_api["homepage_failed"].called


async def test_plugin_info_validation_plugin_load_failed(
    mocked_api: MockRouter,
) -> None:
    """测试验证失败的情况"""
    from src.providers.validation import PublishType, ValidationDict, validate_info

    data = generate_plugin_data(load=False, metadata=False)

    result = validate_info(PublishType.PLUGIN, data, [])

    assert result == snapshot(
        ValidationDict(
            errors=[
                {
                    "type": "plugin.test",
                    "loc": ("load",),
                    "msg": "插件无法正常加载",
                    "input": False,
                    "ctx": {"output": None},
                }
            ],
            info=None,
            raw_data={
                "author": "author",
                "module_name": "module_name",
                "project_link": "project_link",
                "tags": '[{"label": "test", "color": "#ffffff"}]',
                "name": "name",
                "desc": "desc",
                "homepage": "https://nonebot.dev",
                "type": "application",
                "supported_adapters": None,
                "skip_test": False,
                "metadata": False,
                "author_id": 1,
                "load": False,
                "version": "0.0.1",
                "test_output": "test_output",
                "time": "2023-09-01T00:00:00+00:00Z",
            },
            type=PublishType.PLUGIN,
            valid_data={
                "module_name": "module_name",
                "project_link": "project_link",
                "time": "2023-09-01T00:00:00+00:00Z",
                "name": "name",
                "desc": "desc",
                "author": "author",
                "author_id": 1,
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "type": "application",
                "supported_adapters": None,
                "metadata": False,
                "skip_test": False,
                "version": "0.0.1",
                "test_output": "test_output",
            },
        )
    )

    assert mocked_api["homepage"].called
