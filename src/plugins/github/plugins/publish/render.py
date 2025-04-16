from datetime import datetime
from pathlib import Path

import jinja2

from src.plugins.github import plugin_config
from src.providers.constants import TIME_ZONE
from src.providers.docker_test import DockerTestResult
from src.providers.utils import dumps_json
from src.providers.validation import ValidationDict
from src.providers.validation.models import PublishType

from .constants import COMMENT_CARD_TEMPLATE, LOC_NAME_MAP


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
    dt = dt.astimezone(tz=TIME_ZONE)
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

    valid_data = result.valid_data.copy()

    if result.type == PublishType.PLUGIN:
        # https://github.com/he0119/action-test/actions/runs/4469672520
        # 仅在测试通过或跳过测试时显示
        # 如果 load 为 False 的时候 valid_data 里面没有 load 字段，所以直接用 raw_data
        if result.raw_data["load"] or result.raw_data["skip_test"]:
            valid_data["action_url"] = (
                f"https://github.com/{plugin_config.github_repository}/actions/runs/{plugin_config.github_run_id}"
            )
    # 如果 tags 字段为空则不显示
    if not valid_data.get("tags"):
        valid_data.pop("tags", None)

    # 仅显示必要字段
    display_keys = [
        "homepage",
        "project_link",
        "tags",
        "type",
        "supported_adapters",
        "action_url",
        "version",
        "time",
    ]

    # 按照 display_keys 顺序展示数据
    data = {key: valid_data[key] for key in display_keys if key in valid_data}

    card: list[str] = []
    if homepage := data.get("homepage"):
        card.append(COMMENT_CARD_TEMPLATE.format(
            name="主页",
            head="HOMEPAGE",
            content=homepage,
            color="green",
            url=homepage,
        ))
    if action_url := data.get("action_url"):
        card.append(COMMENT_CARD_TEMPLATE.format(
            name="测试结果",
            head="RESULT",
            content="OK" if result.valid else "ERROR",
            color="green" if result.valid else "red",
            url=action_url,
        ))

    template = env.get_template("comment.md.jinja")
    return await template.render_async(
        card=" ".join(card),
        action_url=action_url,
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
