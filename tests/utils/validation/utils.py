import json


def generate_adapter_data(
    name: str = "name",
    desc: str = "desc",
    author: str = "author",
    module_name: str = "module_name",
    project_link: str = "project_link",
    homepage: str = "https://nonebot.dev",
    tags: list = [{"label": "test", "color": "#ffffff"}],
):
    return {
        "name": name,
        "desc": desc,
        "author": author,
        "module_name": module_name,
        "project_link": project_link,
        "homepage": homepage,
        "tags": json.dumps(tags),
    }


def generate_bot_data(
    name: str = "name",
    desc: str = "desc",
    author: str = "author",
    homepage: str = "https://nonebot.dev",
    tags: list | str = [{"label": "test", "color": "#ffffff"}],
):
    if isinstance(tags, list):
        tags = json.dumps(tags)
    return {
        "name": name,
        "desc": desc,
        "author": author,
        "homepage": homepage,
        "tags": tags,
    }


def generate_plugin_data(
    author: str = "author",
    module_name: str = "module_name",
    project_link: str = "project_link",
    tags: list = [{"label": "test", "color": "#ffffff"}],
):
    return {
        "author": author,
        "module_name": module_name,
        "project_link": project_link,
        "tags": json.dumps(tags),
    }
