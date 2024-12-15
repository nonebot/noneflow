from inline_snapshot import snapshot
from respx import MockRouter

from tests.providers.validation.utils import generate_driver_data


async def test_driver_info_validation_success(mocked_api: MockRouter) -> None:
    """测试验证成功的情况"""
    from src.providers.validation import DriverPublishInfo, PublishType, validate_info

    data = generate_driver_data()

    result = validate_info(PublishType.DRIVER, data, [])

    assert result.valid
    assert result.type == PublishType.DRIVER
    assert result.raw_data == snapshot(
        {
            "name": "name",
            "desc": "desc",
            "author": "author",
            "module_name": "module_name",
            "project_link": "project_link",
            "homepage": "https://nonebot.dev",
            "tags": '[{"label": "test", "color": "#ffffff"}]',
            "author_id": 1,
            "time": "2023-09-01T00:00:00.000000Z",
            "version": "0.0.1",
        }
    )

    assert isinstance(result.info, DriverPublishInfo)
    assert result.errors == []

    assert mocked_api["homepage"].called
    assert mocked_api["pypi_project_link"].called


async def test_driver_info_validation_none(mocked_api: MockRouter) -> None:
    """内置驱动器 none 的情况"""
    from src.providers.validation import DriverPublishInfo, PublishType, validate_info

    data = generate_driver_data(project_link="", module_name="~none")

    result = validate_info(PublishType.DRIVER, data, [])

    assert result.valid
    assert result.type == PublishType.DRIVER
    assert result.raw_data == snapshot(
        {
            "name": "name",
            "desc": "desc",
            "author": "author",
            "module_name": "~none",
            "project_link": "",
            "homepage": "https://nonebot.dev",
            "tags": '[{"label": "test", "color": "#ffffff"}]',
            "author_id": 1,
            "time": "2024-10-31T13:47:14.152851Z",
            "version": "2.4.0",
        }
    )

    assert isinstance(result.info, DriverPublishInfo)
    assert result.errors == []

    assert mocked_api["homepage"].called
    assert mocked_api["pypi_nonebot2"].called


async def test_driver_info_validation_fastapi(mocked_api: MockRouter) -> None:
    """内置驱动器 fastapi 的情况"""
    from src.providers.validation import DriverPublishInfo, PublishType, validate_info

    data = generate_driver_data(
        project_link="nonebot2[fastapi]", module_name="~fastapi"
    )

    result = validate_info(PublishType.DRIVER, data, [])

    assert result.valid
    assert result.type == PublishType.DRIVER
    assert result.raw_data == snapshot(
        {
            "name": "name",
            "desc": "desc",
            "author": "author",
            "module_name": "~fastapi",
            "project_link": "nonebot2[fastapi]",
            "homepage": "https://nonebot.dev",
            "tags": '[{"label": "test", "color": "#ffffff"}]',
            "author_id": 1,
            "time": "2024-10-31T13:47:14.152851Z",
            "version": "2.4.0",
        }
    )

    assert isinstance(result.info, DriverPublishInfo)
    assert result.errors == []

    assert mocked_api["homepage"].called
    assert mocked_api["pypi_nonebot2"].called
