from respx import MockRouter

from tests.utils.validation.utils import generate_adapter_data


async def test_pypi_project_name_invalid(mocked_api: MockRouter) -> None:
    """测试 PyPI 项目名错误的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_adapter_data(project_link="project_link/")

    result = validate_info(PublishType.ADAPTER, data)

    assert not result["valid"]
    assert "project_link" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("project_link",)
    assert result["errors"][0]["type"] == "project_link.name"

    assert mocked_api["homepage"].called


async def test_module_name_invalid(mocked_api: MockRouter) -> None:
    """测试模块名称不正确的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_adapter_data(module_name="1module_name")

    result = validate_info(PublishType.ADAPTER, data)

    assert not result["valid"]
    assert "module_name" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("module_name",)
    assert result["errors"][0]["type"] == "module_name"

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
    assert result["errors"]
    assert result["errors"][0]["loc"] == ()
    assert result["errors"][0]["type"] == "duplication"

    assert not mocked_api["project_link1"].called
    assert not mocked_api["homepage"].called


async def test_name_too_long(mocked_api: MockRouter) -> None:
    """测试名称过长的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_adapter_data(
        name="looooooooooooooooooooooooooooooooooooooooooooooooooooooooong"
    )

    result = validate_info(PublishType.ADAPTER, data)

    assert not result["valid"]
    assert "name" not in result["data"]
    assert result["errors"]
    assert result["errors"][0]["loc"] == ("name",)
    assert result["errors"][0]["type"] == "string_too_long"
    assert result["errors"][0]["msg"] == "字符串长度不能超过 50 个字符"

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called
