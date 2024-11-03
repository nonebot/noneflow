from pathlib import Path

import jinja2
from pydantic_core import PydanticCustomError

from .validation import RemoveInfo

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
    enable_async=True,
    lstrip_blocks=True,
    trim_blocks=True,
    autoescape=True,
    keep_trailing_newline=True,
)


async def render_comment(result: RemoveInfo, pr_url: str) -> str:
    """将验证结果转换为评论内容"""
    title = f"{result.publish_type}: remove {result.name}"

    template = env.get_template("comment.md.jinja")
    return await template.render_async(title=title, pr_url=pr_url, valid=True, error=[])


async def render_error(exception: PydanticCustomError):
    """将错误转换成评论内容"""
    template = env.get_template("comment.md.jinja")
    return await template.render_async(
        title="Error", valid=False, error=exception.message()
    )
