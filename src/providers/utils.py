import json
from functools import cache
from pathlib import Path
from typing import Any

import httpx
import pyjson5
from pydantic_core import to_jsonable_python


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
def get_pypi_data(project_link: str) -> dict[str, Any]:
    """获取 PyPI 数据"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    }
    url = f"https://pypi.org/pypi/{project_link}/json"
    try:
        r = httpx.get(url, headers=headers)
    except Exception as e:
        raise ValueError(f"获取 PyPI 数据失败：{e}")
    if r.status_code != 200:
        raise ValueError(f"获取 PyPI 数据失败：{r.text}")
    return load_json(r.text)


def get_latest_version(project_link: str) -> str:
    """获取插件的最新版本号"""
    data = get_pypi_data(project_link)
    return data["info"]["version"]


def get_upload_time(project_link: str) -> str:
    """获取插件的上传时间"""
    data = get_pypi_data(project_link)
    return data["urls"][0]["upload_time_iso_8601"]
