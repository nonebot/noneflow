from respx import MockRouter

from tests.utils.validation.utils import generate_adapter_data


async def test_project_link_invalid(mocked_api: MockRouter) -> None:
    """测试 PyPI 项目名错误的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_adapter_data(project_link="project_link/")

    result = validate_info(PublishType.ADAPTER, data)

    assert not result["valid"]
    assert "project_link" not in result["data"]
    assert result["errors"] == [
        {
            "type": "project_link.name",
            "loc": ("project_link",),
            "msg": "PyPI 项目名不符合规范",
            "input": "project_link/",
        }
    ]

    assert mocked_api["homepage"].called


async def test_module_name_invalid(mocked_api: MockRouter) -> None:
    """测试模块名称不正确的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_adapter_data(module_name="1module_name")

    result = validate_info(PublishType.ADAPTER, data)

    assert not result["valid"]
    assert "module_name" not in result["data"]
    assert result["errors"] == [
        {
            "type": "module_name",
            "loc": ("module_name",),
            "msg": "包名不符合规范",
            "input": "1module_name",
        }
    ]

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called


async def test_name_duplication(mocked_api: MockRouter) -> None:
    """测试名称重复的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_adapter_data(
        module_name="module_name1",
        project_link="project_link1",
        previous_data=[
            {
                "module_name": "module_name1",
                "project_link": "project_link1",
                "name": "name",
                "desc": "desc",
                "author": "author",
            }
        ],
    )

    result = validate_info(PublishType.ADAPTER, data)

    assert not result["valid"]
    assert not result["data"]
    assert result["errors"] == [
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
                "previous_data": [
                    {
                        "module_name": "module_name1",
                        "project_link": "project_link1",
                        "name": "name",
                        "desc": "desc",
                        "author": "author",
                    }
                ],
            },
            "ctx": {"project_link": "project_link1", "module_name": "module_name1"},
        }
    ]

    assert not mocked_api["project_link1"].called
    assert not mocked_api["homepage"].called
