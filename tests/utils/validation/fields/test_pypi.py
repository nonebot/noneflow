from inline_snapshot import snapshot
from respx import MockRouter

from tests.utils.validation.utils import generate_adapter_data


async def test_project_link_invalid(mocked_api: MockRouter) -> None:
    """测试 PyPI 项目名错误的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_adapter_data(project_link="project_link/")

    result = validate_info(PublishType.ADAPTER, data, [])

    assert not result.valid
    assert result.type == PublishType.ADAPTER
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "time": "2023-10-01T00:00:00+00:00Z",
            "name": "name",
            "desc": "desc",
            "author": "author",
            "author_id": 1,
            "homepage": "https://nonebot.dev",
            "tags": [{"label": "test", "color": "#ffffff"}],
        }
    )
    assert result.info is None
    assert result.errors == snapshot(
        [
            {
                "type": "project_link.name",
                "loc": ("project_link",),
                "msg": "PyPI 项目名不符合规范",
                "input": "project_link/",
            }
        ]
    )

    assert mocked_api["homepage"].called


async def test_module_name_invalid(mocked_api: MockRouter) -> None:
    """测试模块名称不正确的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_adapter_data(module_name="1module_name")

    result = validate_info(PublishType.ADAPTER, data, [])

    assert not result.valid
    assert result.type == PublishType.ADAPTER
    assert result.valid_data == snapshot(
        {
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00+00:00Z",
            "name": "name",
            "desc": "desc",
            "author": "author",
            "author_id": 1,
            "homepage": "https://nonebot.dev",
            "tags": [{"label": "test", "color": "#ffffff"}],
        }
    )
    assert result.info is None
    assert result.errors == [
        snapshot(
            {
                "type": "module_name",
                "loc": ("module_name",),
                "msg": "包名不符合规范",
                "input": "1module_name",
            }
        )
    ]

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_name_duplication(mocked_api: MockRouter) -> None:
    """测试名称重复的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_adapter_data(
        module_name="module_name1",
        project_link="project_link1",
    )
    previous_data = [
        {
            "module_name": "module_name1",
            "project_link": "project_link1",
            "author_id": 1,
            "name": "name",
            "desc": "desc",
        }
    ]

    result = validate_info(PublishType.ADAPTER, data, previous_data)

    assert not result.valid
    assert result.type == PublishType.ADAPTER
    assert result.valid_data == snapshot({})
    assert result.info is None
    assert result.errors == snapshot(
        [
            {
                "type": "duplication",
                "loc": (),
                "msg": "PyPI 项目名 project_link1 加包名 module_name1 的值与商店重复",
                "input": {
                    "name": "name",
                    "desc": "desc",
                    "author": "author",
                    "module_name": "module_name1",
                    "project_link": "project_link1",
                    "homepage": "https://nonebot.dev",
                    "tags": '[{"label": "test", "color": "#ffffff"}]',
                    "author_id": 1,
                },
                "ctx": {"project_link": "project_link1", "module_name": "module_name1"},
            }
        ]
    )

    assert not mocked_api["project_link1"].called
    assert not mocked_api["homepage"].called


async def test_name_duplication_previos_data_missing(mocked_api: MockRouter) -> None:
    """没有提供 previos_data 的情况

    获取网络数据失败
    """
    from src.providers.validation import PublishType, validate_info

    data = generate_adapter_data(
        module_name="module_name1", project_link="project_link1"
    )

    result = validate_info(PublishType.ADAPTER, data, None)

    assert not result.valid
    assert result.type == PublishType.ADAPTER
    assert result.valid_data == snapshot({})
    assert result.info is None
    assert result.errors == snapshot(
        [
            {
                "type": "previous_data",
                "loc": (),
                "msg": "未获取到数据列表",
                "input": {
                    "name": "name",
                    "desc": "desc",
                    "author": "author",
                    "module_name": "module_name1",
                    "project_link": "project_link1",
                    "homepage": "https://nonebot.dev",
                    "tags": '[{"label": "test", "color": "#ffffff"}]',
                    "author_id": 1,
                },
            }
        ]
    )

    assert not mocked_api["project_link1"].called
    assert not mocked_api["homepage"].called
