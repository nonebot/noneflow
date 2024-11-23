import pytest
from respx import MockRouter

from src.providers.constants import STORE_ADAPTERS_URL


async def test_load_json_failed(mocked_api: MockRouter):
    """测试加载 json 失败"""
    from src.providers.utils import load_json_from_web

    mocked_api.get(STORE_ADAPTERS_URL).respond(404)

    with pytest.raises(ValueError, match="下载文件失败："):
        load_json_from_web(STORE_ADAPTERS_URL)


async def test_get_pypi_data_failed(mocked_api: MockRouter):
    """获取 PyPI 数据失败"""
    from src.providers.utils import get_pypi_data

    with pytest.raises(ValueError, match="获取 PyPI 数据失败："):
        get_pypi_data("project_link_failed")
