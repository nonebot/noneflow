from pathlib import Path
from typing import TYPE_CHECKING

import jinja2

if TYPE_CHECKING:
    from results import ValidationResult


env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
    enable_async=True,
    trim_blocks=True,
    autoescape=True,
    keep_trailing_newline=True,
)


async def results_to_comment(result: "ValidationResult", reuse: bool = False) -> str:
    """将验证结果转换为评论内容"""
    pass_data = [item for item in result.results if item["type"] == "pass"]
    fail_data = [item for item in result.results if item["type"] == "fail"]
    title = f"{result.type.value}: {result.name}"

    template = env.get_template("comment.md.jinja")
    return await template.render_async(
        title=title,
        is_valid=result.valid,
        data=result._data,
        pass_data=pass_data,
        fail_data=fail_data,
        reuse=reuse,
    )


async def results_to_registry(result: "ValidationResult") -> str:
    """将验证结果转换为注册表内容"""
    pass_data = [item for item in result.results if item["type"] == "pass"]
    fail_data = [item for item in result.results if item["type"] == "fail"]

    template = env.get_template("registry.html.jinja")
    return await template.render_async(
        is_valid=result.valid,
        data=result._data,
        pass_data=pass_data,
        fail_data=fail_data,
    )
