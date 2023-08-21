from collections import OrderedDict

from respx import MockRouter

from tests.utils.validation.utils import generate_adapter_data


async def test_plugin_info_validation_success(mocked_api: MockRouter) -> None:
    """测试验证成功的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_adapter_data()

    result = validate_info(PublishType.ADAPTER, data)

    assert result["valid"]
    assert OrderedDict(result["data"]) == OrderedDict(
        module_name="module_name",
        project_link="project_link",
        name="name",
        desc="desc",
        author="author",
        homepage="https://nonebot.dev",
        tags=[{"label": "test", "color": "#ffffff"}],
        is_official=False,
    )

    assert mocked_api["homepage"].called


async def test_bot_info_validation_failed(mocked_api: MockRouter) -> None:
    """测试验证失败的情况"""
    from src.utils.validation import PublishType, validate_info

    data = generate_adapter_data(
        homepage="https://www.baidu.com",
        tags=[
            {"label": "test", "color": "#ffffff"},
            {"label": "testtoolong", "color": "#fffffff"},
        ],
    )

    result = validate_info(PublishType.ADAPTER, data)

    assert not result["valid"]
    assert "homepage" not in result["data"]
    assert "tags" not in result["data"]
    assert result["errors"]

    assert mocked_api["homepage_failed"].called
