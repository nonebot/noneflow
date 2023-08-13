import json
from typing import Any


def exclude_none(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def generate_adapter_data(
    name: str | None = "name",
    desc: str | None = "desc",
    author: str | None = "author",
    module_name: str | None = "module_name",
    project_link: str | None = "project_link",
    homepage: str | None = "https://nonebot.dev",
    tags: list | None = [{"label": "test", "color": "#ffffff"}],
    previous_data: list[Any] | None = [],
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
            "previous_data": previous_data,
        }
    )


def generate_bot_data(
    name: str | None = "name",
    desc: str | None = "desc",
    author: str | None = "author",
    homepage: str | None = "https://nonebot.dev",
    tags: list | str | None = [{"label": "test", "color": "#ffffff"}],
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
    supported_adapters: list[str] | None = None,
    skip_plugin_test: bool | None = False,
    plugin_test_result: bool | None = True,
    plugin_test_output: str | None = "plugin_test_output",
    previous_data: list[Any] | None = [],
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
            "skip_plugin_test": skip_plugin_test,
            "plugin_test_result": plugin_test_result,
            "plugin_test_output": plugin_test_output,
            "previous_data": previous_data,
            "github_repository": "github",
            "github_run_id": "123456",
        }
    )
