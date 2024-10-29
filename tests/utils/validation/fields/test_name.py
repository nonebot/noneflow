from inline_snapshot import snapshot
from respx import MockRouter

from tests.utils.validation.utils import generate_adapter_data


async def test_name_too_long(mocked_api: MockRouter) -> None:
    """测试名称过长的情况"""
    from src.providers.validation import PublishType, validate_info

    data = generate_adapter_data(
        name="looooooooooooooooooooooooooooooooooooooooooooooooooooooooong"
    )

    result = validate_info(PublishType.ADAPTER, data, [])

    assert not result.valid
    assert result.type == PublishType.ADAPTER
    assert result.valid_data == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "time": "2023-09-01T00:00:00+00:00Z",
            "desc": "desc",
            "author": "author",
            "homepage": "https://nonebot.dev",
            "author_id": 1,
            "tags": [{"label": "test", "color": "#ffffff"}],
        }
    )
    assert result.info is None
    assert result.errors == snapshot(
        [
            {
                "type": "string_too_long",
                "loc": ("name",),
                "msg": "字符串长度不能超过 50 个字符",
                "input": "looooooooooooooooooooooooooooooooooooooooooooooooooooooooong",
                "ctx": {"max_length": 50},
            }
        ]
    )

    assert mocked_api["project_link"].called
    assert mocked_api["homepage"].called
