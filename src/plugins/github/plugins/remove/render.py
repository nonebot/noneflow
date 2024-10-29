from pathlib import Path

import jinja2
from pydantic_core import PydanticCustomError

from src.providers.validation import ValidationDict

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
    enable_async=True,
    lstrip_blocks=True,
    trim_blocks=True,
    autoescape=True,
    keep_trailing_newline=True,
)


async def render_comment(result: ValidationDict) -> str:
    """将验证结果转换为评论内容"""
    title = f"{result.type}: remove {result.name}"

    template = env.get_template("comment.md.jinja")
    return await template.render_async(title=title, valid=True, error=[])


async def render_error(exception: PydanticCustomError):
    """将错误转换成评论内容"""
    template = env.get_template("comment.md.jinja")
    return await template.render_async(title="Error", valid=False, error=exception)
