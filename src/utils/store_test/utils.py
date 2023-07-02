import json
from pathlib import Path


def load_json(path: Path) -> dict:
    """加载 JSON 文件"""
    if not path.exists():
        raise Exception(f"文件 {path} 不存在")

    with open(path, encoding="utf8") as f:
        return json.load(f)


def dump_json(path: Path, data: dict):
    """保存 JSON 文件

    为减少文件大小，还需手动设置 separators
    """
    with open(path, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
