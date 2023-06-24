import json
from pathlib import Path


def load_json(path: Path) -> dict:
    """加载 JSON 文件"""
    if not path.exists():
        raise Exception(f"文件 {path} 不存在")

    with open(path, encoding="utf8") as f:
        return json.load(f)
