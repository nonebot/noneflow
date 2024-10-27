from inline_snapshot import snapshot
from respx import MockRouter

from tests.utils.validation.utils import generate_adapter_data


async def test_adapter_info_validation_success(mocked_api: MockRouter) -> None:
    """测试验证成功的情况"""
    from src.providers.validation import AdapterPublishInfo, PublishType, validate_info

    data, context = generate_adapter_data()

    result = validate_info(PublishType.ADAPTER, data, context)

    assert result.valid
    assert result.type == PublishType.ADAPTER
    assert result.raw_data == snapshot(
        {
            "name": "name",
            "desc": "desc",
            "author": "author",
            "module_name": "module_name",
            "project_link": "project_link",
            "homepage": "https://nonebot.dev",
            "tags": '[{"label": "test", "color": "#ffffff"}]',
            "previous_data": [],
            "author_id": 1,
            "time": "2023-09-01T00:00:00+00:00Z",
        }
    )
    assert result.context == snapshot(
        {
            "previous_data": [],
            "valid_data": {
                "module_name": "module_name",
                "project_link": "project_link",
                "time": "2023-09-01T00:00:00+00:00Z",
                "name": "name",
                "desc": "desc",
                "author": "author",
                "author_id": 1,
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
            },
        }
    )
    assert isinstance(result.info, AdapterPublishInfo)
    assert result.errors == []

    assert mocked_api["homepage"].called


async def test_adapter_info_validation_failed(mocked_api: MockRouter) -> None:
    """测试验证失败的情况"""
    from src.providers.validation import PublishType, validate_info
    from src.providers.validation.models import ValidationDict

    data, context = generate_adapter_data(
        module_name="module_name/",
        project_link="project_link_failed",
        homepage="https://www.baidu.com",
        tags=[
            {"label": "test", "color": "#ffffff"},
            {"label": "testtoolong", "color": "#fffffff"},
        ],
    )

    result = validate_info(PublishType.ADAPTER, data, context)

    assert result == snapshot(
        ValidationDict(
            context={
                "previous_data": [],
                "valid_data": {
                    "time": None,
                    "name": "name",
                    "desc": "desc",
                    "author": "author",
                    "author_id": 1,
                },
            },
            errors=[
                {
                    "type": "module_name",
                    "loc": ("module_name",),
                    "msg": "包名不符合规范",
                    "input": "module_name/",
                },
                {
                    "type": "project_link.not_found",
                    "loc": ("project_link",),
                    "msg": "PyPI 项目名不存在",
                    "input": "project_link_failed",
                },
                {
                    "type": "homepage",
                    "loc": ("homepage",),
                    "msg": "项目主页无法访问",
                    "input": "https://www.baidu.com",
                    "ctx": {"status_code": 404, "msg": ""},
                },
                {
                    "type": "string_too_long",
                    "loc": ("tags", 1, "label"),
                    "msg": "字符串长度不能超过 10 个字符",
                    "input": "testtoolong",
                    "ctx": {"max_length": 10},
                },
                {
                    "type": "color_error",
                    "loc": ("tags", 1, "color"),
                    "msg": "颜色格式不正确",
                    "input": "#fffffff",
                },
            ],
            info=None,
            raw_data={
                "name": "name",
                "desc": "desc",
                "author": "author",
                "module_name": "module_name/",
                "project_link": "project_link_failed",
                "homepage": "https://www.baidu.com",
                "tags": '[{"label": "test", "color": "#ffffff"}, {"label": "testtoolong", "color": "#fffffff"}]',
                "previous_data": [],
                "author_id": 1,
                "time": None,
            },
            type=PublishType.ADAPTER,
        )
    )

    assert mocked_api["homepage_failed"].called
