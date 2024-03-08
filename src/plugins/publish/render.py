from pathlib import Path
from typing import TYPE_CHECKING

import jinja2

from src.utils.validation.models import PublishType

from .config import plugin_config
from .constants import LOC_NAME_MAP

if TYPE_CHECKING:
    from src.utils.validation import ValidationDict


def tags_to_str(tags: list[dict]) -> str:
    """将标签列表转换为字符串"""
    return ", ".join([f"{tag['label']}-{tag['color']}" for tag in tags])


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


async def render_comment(result: "ValidationDict", reuse: bool = False) -> str:
    """将验证结果转换为评论内容"""
    title = f"{result['type'].value}: {result['name']}"

    # 有些数据不需要显示
    result["data"].pop("is_official", None)
    result["data"].pop("module_name", None)
    result["data"].pop("name", None)
    result["data"].pop("desc", None)
    result["data"].pop("author", None)
    if not result["data"].get("tags", []):
        result["data"].pop("tags", None)

    if result["type"] == PublishType.PLUGIN:
        # https://github.com/he0119/action-test/actions/runs/4469672520
        if plugin_config.plugin_test_result or plugin_config.skip_plugin_test:
            result["data"]["action_url"] = (
                f"https://github.com/{plugin_config.github_repository}/actions/runs/{plugin_config.github_run_id}"
            )

    template = env.get_template("comment.md.jinja")
    return await template.render_async(
        reuse=reuse,
        title=title,
        valid=result["valid"],
        data=result["data"],
        errors=result["errors"],
        skip_plugin_test=plugin_config.skip_plugin_test,
    )
