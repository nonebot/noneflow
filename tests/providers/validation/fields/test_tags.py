import json

from inline_snapshot import snapshot
from respx import MockRouter

from tests.providers.validation.utils import generate_plugin_data


async def test_tags_color_missing(mocked_api: MockRouter) -> None:
    """测试标签缺少颜色的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_plugin_data(tags=[{"label": "test"}])

    result = validate_info(PublishType.PLUGIN, data, [])

    assert not result.valid
    assert result.type == PublishType.PLUGIN
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00.000000Z",
            "name": "name",
            "desc": "desc",
            "author": "author",
            "author_id": 1,
            "homepage": "https://nonebot.dev",
            "type": "application",
            "supported_adapters": None,
            "load": True,
            "metadata": True,
            "skip_test": False,
            "version": "0.0.1",
            "test_output": "test_output",
        }
    )
    assert result.info is None
    assert result.errors == [
        snapshot(
            {
                "type": "missing",
                "loc": ("tags", 0, "color"),
                "msg": "字段不存在",
                "input": {"label": "test"},
            }
        )
    ]

    assert mocked_api["pypi_project_link"].called
    assert mocked_api["homepage"].called


async def test_tags_color_invalid(mocked_api: MockRouter) -> None:
    """测试标签颜色不正确的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_plugin_data(tags=[{"label": "test", "color": "#adbcdef"}])

    result = validate_info(PublishType.PLUGIN, data, [])

    assert not result.valid
    assert result.type == PublishType.PLUGIN
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00.000000Z",
            "name": "name",
            "desc": "desc",
            "author": "author",
            "author_id": 1,
            "homepage": "https://nonebot.dev",
            "type": "application",
            "supported_adapters": None,
            "load": True,
            "metadata": True,
            "skip_test": False,
            "version": "0.0.1",
            "test_output": "test_output",
        }
    )
    assert result.info is None
    assert result.errors == [
        snapshot(
            {
                "type": "color_error",
                "loc": ("tags", 0, "color"),
                "msg": "颜色格式不正确",
                "input": "#adbcdef",
            }
        )
    ]

    assert mocked_api["pypi_project_link"].called
    assert mocked_api["homepage"].called


async def test_tags_label_invalid(mocked_api: MockRouter) -> None:
    """测试标签名称不正确的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_plugin_data(tags=[{"label": "12345678901", "color": "#adbcde"}])

    result = validate_info(PublishType.PLUGIN, data, [])

    assert not result.valid
    assert result.type == PublishType.PLUGIN
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00.000000Z",
            "name": "name",
            "desc": "desc",
            "author": "author",
            "author_id": 1,
            "homepage": "https://nonebot.dev",
            "type": "application",
            "supported_adapters": None,
            "load": True,
            "metadata": True,
            "skip_test": False,
            "version": "0.0.1",
            "test_output": "test_output",
        }
    )
    assert result.info is None
    assert result.errors == [
        snapshot(
            {
                "type": "string_too_long",
                "loc": ("tags", 0, "label"),
                "msg": "字符串长度不能超过 10 个字符",
                "input": "12345678901",
                "ctx": {"max_length": 10},
            }
        )
    ]

    assert mocked_api["pypi_project_link"].called
    assert mocked_api["homepage"].called


async def test_tags_number_invalid(mocked_api: MockRouter) -> None:
    """测试标签数量不正确的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_plugin_data(
        tags=[
            {"label": "1", "color": "#ffffff"},
            {"label": "2", "color": "#ffffff"},
            {"label": "3", "color": "#ffffff"},
            {"label": "4", "color": "#ffffff"},
        ]
    )

    result = validate_info(PublishType.PLUGIN, data, [])

    assert not result.valid
    assert result.type == PublishType.PLUGIN
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00.000000Z",
            "name": "name",
            "desc": "desc",
            "author": "author",
            "author_id": 1,
            "homepage": "https://nonebot.dev",
            "type": "application",
            "supported_adapters": None,
            "load": True,
            "metadata": True,
            "skip_test": False,
            "version": "0.0.1",
            "test_output": "test_output",
        }
    )
    assert result.info is None
    assert result.errors == [
        snapshot(
            {
                "type": "too_long",
                "loc": ("tags",),
                "msg": "列表长度不能超过 3 个元素",
                "input": [
                    {"label": "1", "color": "#ffffff"},
                    {"label": "2", "color": "#ffffff"},
                    {"label": "3", "color": "#ffffff"},
                    {"label": "4", "color": "#ffffff"},
                ],
                "ctx": {"field_type": "List", "max_length": 3, "actual_length": 4},
            }
        )
    ]

    assert mocked_api["pypi_project_link"].called
    assert mocked_api["homepage"].called


async def test_tags_json_invalid(mocked_api: MockRouter) -> None:
    """测试标签 json 格式不正确的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_plugin_data()
    data["tags"] = json.dumps([{"label": "1", "color": "#ffffff"}]) + "1"

    result = validate_info(PublishType.PLUGIN, data, [])

    assert not result.valid
    assert result.type == PublishType.PLUGIN
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00.000000Z",
            "name": "name",
            "desc": "desc",
            "author": "author",
            "author_id": 1,
            "homepage": "https://nonebot.dev",
            "type": "application",
            "supported_adapters": None,
            "load": True,
            "metadata": True,
            "skip_test": False,
            "version": "0.0.1",
            "test_output": "test_output",
        }
    )
    assert result.info is None
    assert result.errors == [
        snapshot(
            {
                "type": "json_type",
                "loc": ("tags",),
                "msg": "JSON 格式不合法",
                "input": '[{"label": "1", "color": "#ffffff"}]1',
            }
        )
    ]

    assert mocked_api["pypi_project_link"].called
    assert mocked_api["homepage"].called


async def test_tags_json_not_list(mocked_api: MockRouter) -> None:
    """测试标签 json 不是列表的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_plugin_data()
    data["tags"] = json.dumps({"test": "test"})

    result = validate_info(PublishType.PLUGIN, data, [])

    assert not result.valid
    assert result.type == PublishType.PLUGIN
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00.000000Z",
            "name": "name",
            "desc": "desc",
            "author": "author",
            "author_id": 1,
            "homepage": "https://nonebot.dev",
            "type": "application",
            "supported_adapters": None,
            "load": True,
            "metadata": True,
            "skip_test": False,
            "version": "0.0.1",
            "test_output": "test_output",
        }
    )
    assert result.info is None
    assert result.errors == [
        snapshot(
            {
                "type": "list_type",
                "loc": ("tags",),
                "msg": "值不是合法的列表",
                "input": {"test": "test"},
            }
        )
    ]

    assert mocked_api["pypi_project_link"].called
    assert mocked_api["homepage"].called


async def test_tags_json_not_dict(mocked_api: MockRouter) -> None:
    """测试标签 json 是列表但列表里不全是字典的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_plugin_data(tags=[{"label": "1", "color": "#ffffff"}, "1"])

    result = validate_info(PublishType.PLUGIN, data, [])

    assert not result.valid
    assert result.type == PublishType.PLUGIN
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00.000000Z",
            "name": "name",
            "desc": "desc",
            "author": "author",
            "author_id": 1,
            "homepage": "https://nonebot.dev",
            "type": "application",
            "supported_adapters": None,
            "load": True,
            "metadata": True,
            "skip_test": False,
            "version": "0.0.1",
            "test_output": "test_output",
        }
    )
    assert result.info is None
    assert result.errors == [
        snapshot(
            {
                "type": "model_type",
                "loc": ("tags", 1),
                "msg": "值不是合法的字典",
                "input": "1",
                "ctx": {"class_name": "Tag"},
            }
        )
    ]

    assert mocked_api["pypi_project_link"].called
    assert mocked_api["homepage"].called
