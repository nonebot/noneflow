from inline_snapshot import snapshot
from respx import MockRouter

from tests.utils.validation.utils import generate_adapter_data


async def test_name_too_long(mocked_api: MockRouter) -> None:
    """测试名称过长的情况"""
    from src.providers.validation import PublishType, validate_info

    data, context = generate_adapter_data(
        name="looooooooooooooooooooooooooooooooooooooooooooooooooooooooong"
    )

    result = validate_info(PublishType.ADAPTER, data, context)

    assert not result.valid
    assert "name" not in result.valid_data
    assert result.errors == [
        snapshot(
            {
                "type": "string_too_long",
                "loc": ("name",),
                "msg": "字符串长度不能超过 50 个字符",
                "input": "looooooooooooooooooooooooooooooooooooooooooooooooooooooooong",
                "ctx": {"max_length": 50},
            }
        )
    ]

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called
