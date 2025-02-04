from pathlib import Path


def find_datetime_loc(path: Path) -> list[str]:
    """
    找到所有包含 `from datetime import datetime` 的相对导入路径
    """
    result: list[str] = []

    def to_module_path(file_path: Path) -> str:
        relative_path = file_path.relative_to(path.parent)
        parts = list(relative_path.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)

    for p in path.rglob("*.py"):
        content = p.read_text("utf-8")
        if "from datetime import datetime" in content:
            result.append(to_module_path(p))
    return result
