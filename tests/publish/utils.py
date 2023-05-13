import json


def generate_issue_body_adapter(
    name: str = "name",
    desc: str = "desc",
    module_name: str = "module_name",
    project_link: str = "project_link",
    homepage: str = "https://v2.nonebot.dev",
    tags: list = [{"label": "test", "color": "#ffffff"}],
):
    return f"""### 适配器名称\n\n{name}\n\n### 适配器描述\n\n{desc}\n\n### PyPI 项目名\n\n{project_link}\n\n### 适配器 import 包名\n\n{module_name}\n\n### 适配器项目仓库/主页链接\n\n{homepage}\n\n### 标签\n\n{json.dumps(tags)}"""


def generate_issue_body_bot(
    name: str = "name",
    desc: str = "desc",
    homepage: str = "https://v2.nonebot.dev",
    tags: list | str = [{"label": "test", "color": "#ffffff"}],
):
    if isinstance(tags, list):
        tags = json.dumps(tags)
    return f"""### 机器人名称\n\n{name}\n\n### 机器人描述\n\n{desc}\n\n### 机器人项目仓库/主页链接\n\n{homepage}\n\n### 标签\n\n{tags}"""


def generate_issue_body_plugin(
    name: str = "name",
    desc: str = "desc",
    module_name: str = "module_name",
    project_link: str = "project_link",
    homepage: str = "https://v2.nonebot.dev",
    tags: list = [{"label": "test", "color": "#ffffff"}],
):
    return f"""### 插件名称\n\n{name}\n\n### 插件描述\n\n{desc}\n\n### PyPI 项目名\n\n{project_link}\n\n### 插件 import 包名\n\n{module_name}\n\n### 插件项目仓库/主页链接\n\n{homepage}\n\n### 标签\n\n{json.dumps(tags)}"""
