import json
from functools import cache
from pathlib import Path
from typing import Any

import httpx
from pydantic_core import to_jsonable_python


def load_json(url: str) -> Any:
    """从网络加载 JSON 文件"""
    r = httpx.get(url)
    if r.status_code != 200:
        raise ValueError(f"下载文件失败：{r.text}")
    return r.json()


def dump_json(path: Path, data: Any):
    """保存 JSON 文件

    为减少文件大小，还需手动设置 separators
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            to_jsonable_python(data), f, ensure_ascii=False, separators=(",", ":")
        )


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
    data = load_json(f"https://api.github.com/users/{name}")
    return data["id"]
