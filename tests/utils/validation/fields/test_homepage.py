from respx import MockRouter

from tests.utils.validation.utils import generate_bot_data


async def test_homepage_failed_http_exception(mocked_api: MockRouter) -> None:
    """测试验证失败的情况，HTTP 请求报错"""
    from src.utils.validation import PublishType, validate_info

    data = generate_bot_data(homepage="exception")

    result = validate_info(PublishType.BOT, data)

    assert not result["valid"]
    assert "homepage" not in result["data"]
    assert result["errors"] == [
        {
            "type": "homepage",
            "loc": ("homepage",),
            "msg": "项目主页无法访问",
            "input": "exception",
            "ctx": {"status_code": -1, "msg": "Mock Error"},
        }
    ]

    assert mocked_api["exception"].called
