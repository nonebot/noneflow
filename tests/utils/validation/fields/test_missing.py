from inline_snapshot import snapshot
from respx import MockRouter

from tests.utils.validation.utils import generate_plugin_data


async def test_fields_missing_plugin(mocked_api: MockRouter) -> None:
    """测试字段缺失的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_plugin_data(
        name=None,
        desc=None,
        homepage=None,
        type=None,
        supported_adapters=None,
        test_output="error",
        load=False,
        metadata=False,
        version=None,
    )
    data["version"] = None

    result = validate_info(PublishType.PLUGIN, data, [])

    assert not result.valid
    assert result.type == PublishType.PLUGIN
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00+00:00",
            "author": "author",
            "author_id": 1,
            "tags": [{"label": "test", "color": "#ffffff"}],
            "supported_adapters": None,
            "metadata": False,
            "skip_test": False,
            "test_output": "error",
        }
    )
    assert result.info is None
    assert result.errors == snapshot(
        [
            {
                "type": "missing",
                "loc": ("name",),
                "msg": "字段不存在",
                "input": {
                    "author": "author",
                    "module_name": "module_name",
                    "project_link": "project_link",
                    "tags": '[{"label": "test", "color": "#ffffff"}]',
                    "supported_adapters": None,
                    "skip_test": False,
                    "metadata": False,
                    "author_id": 1,
                    "load": False,
                    "test_output": "error",
                    "version": None,
                    "time": "2023-09-01T00:00:00+00:00",
                },
            },
            {
                "type": "missing",
                "loc": ("desc",),
                "msg": "字段不存在",
                "input": {
                    "author": "author",
                    "module_name": "module_name",
                    "project_link": "project_link",
                    "tags": '[{"label": "test", "color": "#ffffff"}]',
                    "supported_adapters": None,
                    "skip_test": False,
                    "metadata": False,
                    "author_id": 1,
                    "load": False,
                    "test_output": "error",
                    "version": None,
                    "time": "2023-09-01T00:00:00+00:00",
                },
            },
            {
                "type": "missing",
                "loc": ("homepage",),
                "msg": "字段不存在",
                "input": {
                    "author": "author",
                    "module_name": "module_name",
                    "project_link": "project_link",
                    "tags": '[{"label": "test", "color": "#ffffff"}]',
                    "supported_adapters": None,
                    "skip_test": False,
                    "metadata": False,
                    "author_id": 1,
                    "load": False,
                    "test_output": "error",
                    "version": None,
                    "time": "2023-09-01T00:00:00+00:00",
                },
            },
            {
                "type": "missing",
                "loc": ("type",),
                "msg": "字段不存在",
                "input": {
                    "author": "author",
                    "module_name": "module_name",
                    "project_link": "project_link",
                    "tags": '[{"label": "test", "color": "#ffffff"}]',
                    "supported_adapters": None,
                    "skip_test": False,
                    "metadata": False,
                    "author_id": 1,
                    "load": False,
                    "test_output": "error",
                    "version": None,
                    "time": "2023-09-01T00:00:00+00:00",
                },
            },
            {
                "type": "plugin.test",
                "loc": ("load",),
                "msg": "插件无法正常加载",
                "input": False,
                "ctx": {"output": "error"},
            },
            {
                "type": "string_type",
                "loc": ("version",),
                "msg": "值不是合法的字符串",
                "input": None,
            },
        ]
    )

    assert mocked_api["project_link"].called
    assert not mocked_api["homepage"].called
