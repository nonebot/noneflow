from functools import cache
from typing import Any

import httpx

from src.providers.utils import load_json_from_web


@cache
def get_pypi_data(project_link: str) -> dict[str, Any]:
    """获取 PyPI 数据"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    }
    url = f"https://pypi.org/pypi/{project_link}/json"
    r = httpx.get(url, headers=headers)
    if r.status_code != 200:
        raise ValueError(f"获取 PyPI 数据失败：{r.text}")
    return r.json()


def get_latest_version(project_link: str) -> str:
    """获取插件的最新版本号"""
    data = get_pypi_data(project_link)
    return data["info"]["version"]


def get_upload_time(project_link: str) -> str:
    """获取插件的上传时间"""
    data = get_pypi_data(project_link)
    return data["urls"][0]["upload_time_iso_8601"]


def get_user_id(name: str) -> int:
    """获取用户信息"""
    data = load_json_from_web(f"https://api.github.com/users/{name}")
    return data["id"]
