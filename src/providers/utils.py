import json
import os
from functools import cache
from pathlib import Path
from typing import Any

import httpx
import pyjson5
from pydantic_core import to_jsonable_python

from src.providers.logger import logger


def load_json_from_file(file_path: str | Path):
    """从文件加载 JSON5 文件"""
    with open(file_path, encoding="utf-8") as file:
        return pyjson5.decode_io(file)  # type: ignore


def load_json_from_web(url: str):
    """从网络加载 JSON5 文件"""
    r = httpx.get(url)
    if r.status_code != 200:
        raise ValueError(f"下载文件失败：{r.text}")
    return pyjson5.decode(r.text)


def load_json(text: str):
    """从文本加载 JSON5"""
    return pyjson5.decode(text)


def dumps_json(data: Any, minify: bool = True) -> str:
    """格式化对象"""
    if minify:
        data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    else:
        data = json.dumps(data, ensure_ascii=False, indent=2)
    return data


def dump_json(path: str | Path, data: Any, minify: bool = True) -> None:
    """保存 JSON 文件"""
    data = to_jsonable_python(data)

    with open(path, "w", encoding="utf-8") as f:
        if minify:
            # 为减少文件大小，还需手动设置 separators
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)


def dump_json5(path: Path, data: Any) -> None:
    """保存 JSON5 文件

    手动添加末尾的逗号和换行符
    """
    data = to_jsonable_python(data)

    content = json.dumps(data, ensure_ascii=False, indent=2)
    # 手动添加末尾的逗号和换行符
    # 避免合并时出现冲突
    content = content.replace("}\n]", "},\n]")
    content += "\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


@cache
def get_url(url: str) -> httpx.Response:
    """获取网址"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    }
    return httpx.get(url, follow_redirects=True, headers=headers)


def get_pypi_data(project_link: str) -> dict[str, Any]:
    """获取 PyPI 数据"""

    url = f"https://pypi.org/pypi/{project_link}/json"
    try:
        r = get_url(url)
    except Exception as e:
        raise ValueError(f"获取 PyPI 数据失败：{e}")
    if r.status_code != 200:
        raise ValueError(f"获取 PyPI 数据失败：{r.text}")
    return r.json()


def get_pypi_name(project_link: str) -> str:
    """获取 PyPI 项目名"""
    data = get_pypi_data(project_link)
    return data["info"]["name"]


def get_pypi_version(project_link: str) -> str | None:
    """获取插件的最新版本号"""
    try:
        data = get_pypi_data(project_link)
    except ValueError:
        return None
    return data["info"]["version"]


def get_pypi_upload_time(project_link: str) -> str | None:
    """获取插件的上传时间"""
    try:
        data = get_pypi_data(project_link)
    except ValueError:
        return None
    return data["urls"][0]["upload_time_iso_8601"]


def add_step_summary(summary: str):
    """添加作业摘要"""
    github_step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not github_step_summary:
        logger.warning("未找到 GITHUB_STEP_SUMMARY 环境变量")
        return
    with open(github_step_summary, "a", encoding="utf-8") as f:
        f.write(summary + "\n")
    logger.debug(f"已添加作业摘要：{summary}")


@cache
def get_author_name(author_id: int) -> str:
    """通过作者的ID获取作者名字"""
    url = f"https://api.github.com/user/{author_id}"
    return load_json_from_web(url)["login"]
