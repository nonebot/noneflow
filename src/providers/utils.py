import json
from pathlib import Path
from typing import Any

import httpx
import pyjson5
from pydantic_core import to_jsonable_python


def load_json_from_file(file_path: Path):
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


def encode_json(data: Any, minify: bool = True):
    """格式化对象"""
    if minify:
        json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    else:
        json.dumps(data, ensure_ascii=False, indent=2)


def dump_json(path: Path, data: Any, minify: bool = True) -> None:
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
