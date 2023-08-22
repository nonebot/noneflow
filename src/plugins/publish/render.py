from pathlib import Path
from typing import TYPE_CHECKING

import jinja2

from src.utils.validation.models import PublishType

from .config import plugin_config

if TYPE_CHECKING:
    from src.utils.validation import ValidationDict


def debug_print(*args, **kwargs):
    print(*args, **kwargs)


def tags_to_str(tags: list[dict]) -> str:
    """将标签列表转换为字符串"""
    return ", ".join([f"{tag['label']}-{tag['color']}" for tag in tags])


def supported_adapters_to_str(supported_adapters: list[str] | None) -> str:
    """将支持的适配器列表转换为字符串"""
    if supported_adapters is None:
        return "所有"
    return ", ".join(supported_adapters)


env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
    enable_async=True,
    lstrip_blocks=True,
    trim_blocks=True,
    autoescape=True,
    keep_trailing_newline=True,
)

env.filters["debug_print"] = debug_print
env.filters["tags_to_str"] = tags_to_str
env.filters["supported_adapters_to_str"] = supported_adapters_to_str


async def render_comment(result: "ValidationDict", reuse: bool = False) -> str:
    """将验证结果转换为评论内容"""
    title = f"{result['type'].value}: {result['name']}"

    action_url = None
    if result["type"] == PublishType.PLUGIN:
        # https://github.com/he0119/action-test/actions/runs/4469672520
        if plugin_config.plugin_test_result or plugin_config.skip_plugin_test:
            result["data"][
                "action_url"
            ] = f"https://github.com/{plugin_config.github_repository}/actions/runs/{plugin_config.github_run_id}"

    template = env.get_template("comment.md.jinja")
    return await template.render_async(
        title=title,
        valid=result["valid"],
        reuse=reuse,
        data=result["data"],
        errors=result["errors"],
        skip_plugin_test=plugin_config.skip_plugin_test,
    )
