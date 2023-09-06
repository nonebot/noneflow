import json
from functools import cache
from pathlib import Path
from typing import Any

import httpx


def load_json(path: Path) -> dict:
    """加载 JSON 文件"""
    if not path.exists():
        raise Exception(f"文件 {path} 不存在")

    with open(path, encoding="utf8") as f:
        return json.load(f)


def dump_json(path: Path, data: dict | list):
    """保存 JSON 文件

    为减少文件大小，还需手动设置 separators
    """
    with open(path, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


@cache
def get_pypi_data(project_link: str) -> dict[str, Any]:
    """获取 PyPI 数据"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    }
    url = f"https://pypi.org/pypi/{project_link}/json"
    r = httpx.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    raise ValueError(f"获取 PyPI 数据失败：{r.text}")


def get_latest_version(project_link: str) -> str:
    """获取插件的最新版本号"""
    data = get_pypi_data(project_link)
    return data["info"]["version"]


def get_upload_time(project_link: str) -> str:
    """获取插件的上传时间"""
    data = get_pypi_data(project_link)
    return data["urls"][0]["upload_time_iso_8601"]
