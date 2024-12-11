from pathlib import Path

import jinja2

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
    enable_async=True,
    lstrip_blocks=True,
    trim_blocks=True,
    keep_trailing_newline=True,
)


async def render_runner(module_name: str, deps: list[str]) -> str:
    """生成 runner.py 文件内容"""
    template = env.get_template("runner.py.jinja")

    return await template.render_async(
        module_name=module_name,
        deps=deps,
    )


async def render_fake():
    """生成 fake.py 文件内容"""
    template = env.get_template("fake.py.jinja")

    return await template.render_async()
