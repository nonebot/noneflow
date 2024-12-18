from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import jinja2

from src.plugins.github import plugin_config
from src.providers.docker_test import DockerTestResult
from src.providers.utils import dumps_json
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


def key_to_name(key: str) -> str:
    """将 key 转换为可读名称"""
    return _loc_to_name(key)


def format_time(time: str) -> str:
    """格式化时间"""
    dt = datetime.fromisoformat(time)
    # 转换为中国时区，方便阅读
    dt = dt.astimezone(tz=ZoneInfo("Asia/Shanghai"))
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


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
env.filters["key_to_name"] = key_to_name
env.filters["format_time"] = format_time


async def render_comment(result: ValidationDict, reuse: bool = False) -> str:
    """将验证结果转换为评论内容"""
    title = f"{result.type}: {result.name}"

    # 将 data 字段拷贝一份，避免修改原数据
    valid_data: dict[str, Any] = result.valid_data.copy()

    # 仅显示必要字段
    display_keys = [
        "homepage",
        "tags",
        "project_link",
        "type",
        "supported_adapters",
        "time",
        "version",
    ]

    # 按照 display_keys 顺序展示数据
    data = {key: valid_data[key] for key in display_keys if key in valid_data}

    if not data.get("tags"):
        data.pop("tags", None)

    if result.type == PublishType.PLUGIN:
        # https://github.com/he0119/action-test/actions/runs/4469672520
        # 仅在测试通过或跳过测试时显示
        # 如果 load 为 False 的时候 valid_data 里面没有 load 字段，所以直接用 raw_data
        if result.raw_data["load"] or result.raw_data["skip_test"]:
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


async def render_summary(test_result: DockerTestResult, output: str, project_link: str):
    """将测试结果转换为工作流总结"""
    template = env.get_template("summary.md.jinja")

    return await template.render_async(
        project_link=project_link,
        version=test_result.version,
        load=test_result.load,
        run=test_result.run,
        metadata=dumps_json(test_result.metadata, False)
        if test_result.metadata
        else {},
        output=output,
    )
