from respx import MockRouter

from tests.utils.validation.utils import generate_adapter_data


async def test_name_too_long(mocked_api: MockRouter) -> None:
    """测试名称过长的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_adapter_data(
        name="looooooooooooooooooooooooooooooooooooooooooooooooooooooooong"
    )

    result = validate_info(PublishType.ADAPTER, data)

    assert not result["valid"]
    assert "name" not in result["data"]
    assert result["errors"] == [
        {
            "type": "string_too_long",
            "loc": ("name",),
            "msg": "字符串长度不能超过 50 个字符",
            "input": "looooooooooooooooooooooooooooooooooooooooooooooooooooooooong",
            "ctx": {"max_length": 50},
            "url": "https://errors.pydantic.dev/2.8/v/string_too_long",
        }
    ]

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called
