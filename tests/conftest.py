import pytest

from src.models import check_url


@pytest.fixture(autouse=True, scope="function")
def clear_cache():
    """每次运行前都清除 cache"""
    check_url.cache_clear()
