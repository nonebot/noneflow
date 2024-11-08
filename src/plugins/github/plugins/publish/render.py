from pathlib import Path
from typing import Any

import jinja2

from src.plugins.github import plugin_config
from src.providers.validation import ValidationDict
from src.providers.validation.models import PublishType

from .constants import LOC_NAME_MAP


def tags_to_str(tags: list[dict[str, str]]) -> str:
    """将标签列表转换为字符串"""
    return ", ".join([f"{tag["label"]}-{tag["color"]}" for tag in tags])


def supported_adapters_to_str(supported_adapters: list[str] | None) -> str:
    """将支持的适配器列表转换为字符串"""
    if supported_adapters is None:
        return "所有"
    return ", ".join(supported_adapters)


def _loc_to_name(loc: str) -> str:
    """将 loc 转换为可读名称"""
    if loc in LOC_NAME_MAP:
        return LOC_NAME_MAP[loc]
    return loc


def loc_to_name(loc: list[str | int]) -> str:
    """将 loc 转换为可读名称"""
    return " > ".join([_loc_to_name(str(item)) for item in loc])


env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
    enable_async=True,
    lstrip_blocks=True,
    trim_blocks=True,
    autoescape=True,
    keep_trailing_newline=True,
)

env.filters["tags_to_str"] = tags_to_str
env.filters["supported_adapters_to_str"] = supported_adapters_to_str
env.filters["loc_to_name"] = loc_to_name


async def render_comment(result: ValidationDict, reuse: bool = False) -> str:
    """将验证结果转换为评论内容"""
    title = f"{result.type}: {result.name}"

    # 将 data 字段拷贝一份，避免修改原数据
    data: dict[str, Any] = result.valid_data.copy()

    # 仅显示必要字段
    display_keys = [
        "homepage",
        "tags",
        "project_link",
        "type",
        "supported_adapters",
    ]

    for key in data.copy():
        if key not in display_keys:
            data.pop(key)

    if not data.get("tags"):
        data.pop("tags", None)

    if result.type == PublishType.PLUGIN:
        # https://github.com/he0119/action-test/actions/runs/4469672520
        # 仅在测试通过或跳过测试时显示
        if result.valid_data["load"] or result.valid_data["skip_test"]:
            data["action_url"] = (
                f"https://github.com/{plugin_config.github_repository}/actions/runs/{plugin_config.github_run_id}"
            )

    template = env.get_template("comment.md.jinja")
    return await template.render_async(
        reuse=reuse,
        title=title,
        valid=result.valid,
        data=data,
        errors=result.errors,
        skip_test=result.skip_test,
    )
