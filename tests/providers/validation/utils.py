import json
from typing import Any


def exclude_none(data: dict[str, Any]) -> dict[str, Any]:
    """去除字典中的 None 值

    supported_adapters 字段除外
    """
    return {k: v for k, v in data.items() if v is not None or k == "supported_adapters"}


def generate_adapter_data(
    name: str | None = "name",
    desc: str | None = "desc",
    author: str | None = "author",
    module_name: str | None = "module_name",
    project_link: str | None = "project_link",
    homepage: str | None = "https://nonebot.dev",
    tags: list | None = [{"label": "test", "color": "#ffffff"}],
    author_id: int | None = 1,
):
    return exclude_none(
        {
            "name": name,
            "desc": desc,
            "author": author,
            "module_name": module_name,
            "project_link": project_link,
            "homepage": homepage,
            "tags": json.dumps(tags),
            "author_id": author_id,
        }
    )


def generate_bot_data(
    name: str | None = "name",
    desc: str | None = "desc",
    author: str | None = "author",
    homepage: str | None = "https://nonebot.dev",
    tags: list | str | None = [{"label": "test", "color": "#ffffff"}],
    author_id: int | None = 1,
):
    if isinstance(tags, list):
        tags = json.dumps(tags)
    return exclude_none(
        {
            "name": name,
            "desc": desc,
            "author": author,
            "homepage": homepage,
            "tags": tags,
            "author_id": author_id,
        }
    )


def generate_plugin_data(
    author: str | None = "author",
    module_name: str | None = "module_name",
    project_link: str | None = "project_link",
    tags: list | None = [{"label": "test", "color": "#ffffff"}],
    name: str | None = "name",
    desc: str | None = "desc",
    homepage: str | None = "https://nonebot.dev",
    type: str | None = "application",
    supported_adapters: Any = None,
    skip_test: bool | None = False,
    author_id: int | None = 1,
    test_output: str | None = "test_output",
    load: bool | None = True,
    metadata: bool | None = True,
    version: str | None = "0.0.1",
):
    return exclude_none(
        {
            "author": author,
            "module_name": module_name,
            "project_link": project_link,
            "tags": json.dumps(tags),
            "name": name,
            "desc": desc,
            "homepage": homepage,
            "type": type,
            "supported_adapters": supported_adapters,
            "skip_test": skip_test,
            "metadata": metadata,
            "author_id": author_id,
            "load": load,
            "version": version,
            "test_output": test_output,
        }
    )
