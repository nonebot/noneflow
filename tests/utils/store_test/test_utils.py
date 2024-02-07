import pytest
from respx import MockRouter

from src.utils.constants import STORE_ADAPTERS_URL


async def test_load_json_failed(mocked_api: MockRouter):
    """测试加载 json 失败"""
    from src.utils.store_test.utils import load_json

    mocked_api.get(STORE_ADAPTERS_URL).respond(404)

    with pytest.raises(ValueError) as e:
        load_json(STORE_ADAPTERS_URL)

    assert str(e.value) == "下载文件失败："


async def test_get_pypi_data_failed(mocked_api: MockRouter):
    """获取 PyPI 数据失败"""
    from src.utils.store_test.utils import get_pypi_data

    with pytest.raises(ValueError) as e:
        get_pypi_data("project_link_failed")

    assert str(e.value) == "获取 PyPI 数据失败："
