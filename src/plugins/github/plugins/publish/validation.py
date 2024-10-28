import json
import re
from typing import Any

from githubkit.rest import Issue
from nonebot import logger

from src.plugins.github import plugin_config
from src.plugins.github.models import AuthorInfo
from src.plugins.github.models.issue import IssueHandler
from src.plugins.github.utils import extract_publish_info_from_issue
from src.providers.constants import DOCKER_IMAGES
from src.providers.docker_test import DockerPluginTest, Metadata
from src.providers.validation import PublishType, ValidationDict, validate_info

from .constants import (
    ADAPTER_DESC_PATTERN,
    ADAPTER_HOMEPAGE_PATTERN,
    ADAPTER_MODULE_NAME_PATTERN,
    ADAPTER_NAME_PATTERN,
    BOT_DESC_PATTERN,
    BOT_HOMEPAGE_PATTERN,
    BOT_NAME_PATTERN,
    PLUGIN_CONFIG_PATTERN,
    PLUGIN_DESC_PATTERN,
    PLUGIN_HOMEPAGE_PATTERN,
    PLUGIN_MODULE_NAME_PATTERN,
    PLUGIN_NAME_PATTERN,
    PLUGIN_SUPPORTED_ADAPTERS_PATTERN,
    PLUGIN_TYPE_PATTERN,
    PROJECT_LINK_PATTERN,
    TAGS_PATTERN,
)


def strip_ansi(text: str | None) -> str:
    """去除 ANSI 转义字符"""
    if not text:
        return ""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


async def validate_plugin_info_from_issue(
    issue: Issue, handler: IssueHandler, skip_test: bool | None = None
) -> ValidationDict:
    """从议题中获取插件信息，并且运行插件测试加载且获取插件元信息后进行验证"""
    body = issue.body if issue.body else ""

    # 从议题里提取插件所需信息
    raw_data: dict[str, Any] = extract_publish_info_from_issue(
        {
            "module_name": PLUGIN_MODULE_NAME_PATTERN,
            "project_link": PROJECT_LINK_PATTERN,
            "test_config": PLUGIN_CONFIG_PATTERN,
            "tags": TAGS_PATTERN,
        },
        body,
    )
    # 更新作者信息
    raw_data.update(AuthorInfo.from_issue(issue).model_dump())

    module_name: str = raw_data["module_name"]
    project_link: str = raw_data["project_link"]
    test_config: str = raw_data["test_config"]

    # 获取插件上次的数据
    with plugin_config.input_config.plugin_path.open("r", encoding="utf-8") as f:
        previous_data: list[dict[str, Any]] = json.load(f)

    # 决定是否跳过插件测试
    # 因为在上一步可能已经知道了是否跳过插件测试，所以这里可以传入
    # 如果没有传入，则从 handler 中获取
    if skip_test is None:
        skip_test = await handler.should_skip_test()

    raw_data["skip_test"] = skip_test
    if skip_test:
        # 如果插件被跳过，则从议题获取插件信息
        metadata = extract_publish_info_from_issue(
            {
                "name": PLUGIN_NAME_PATTERN,
                "desc": PLUGIN_DESC_PATTERN,
                "homepage": PLUGIN_HOMEPAGE_PATTERN,
                "type": PLUGIN_TYPE_PATTERN,
                "supported_adapters": PLUGIN_SUPPORTED_ADAPTERS_PATTERN,
            },
            body,
        )
        raw_data.update(metadata)

        raw_data["load"] = False
        raw_data["test_output"] = "插件未进行测试"
        raw_data["metadata"] = bool(metadata)
        logger.info(f"插件已跳过测试，从议题中获取的插件元信息：{metadata}")
    else:
        # 插件不跳过则运行插件测试
        test_result = await DockerPluginTest(
            DOCKER_IMAGES, project_link, module_name, test_config
        ).run("3.12")
        # 去除颜色字符
        test_output = strip_ansi("\n".join(test_result.outputs))
        metadata = test_result.metadata
        if metadata:
            # 从插件测试结果中获得元数据
            raw_data.update(metadata.model_dump())

        raw_data["load"] = test_result.load
        raw_data["test_output"] = test_output
        raw_data["metadata"] = bool(metadata)

        logger.info(f"插件测试结果: {test_result}")
        logger.info(f"插件元数据: {metadata}")

    # 验证插件相关信息
    result = validate_info(PublishType.PLUGIN, raw_data, previous_data)

    if result.valid_data.get("metadata") is None and not skip_test:
        # 如果没有跳过测试且缺少插件元数据，则跳过元数据相关的错误
        # 因为这个时候这些项都会报错，错误在此时没有意义
        metadata_keys = Metadata.model_fields.keys()
        result.errors = [
            error for error in result.errors if error["loc"][0] not in metadata_keys
        ]
        # 元数据缺失时，需要删除元数据相关的字段
        for key in metadata_keys:
            result.valid_data.pop(key, None)

    return result


async def validate_adapter_info_from_issue(issue: Issue) -> ValidationDict:
    """从议题中提取适配器信息"""
    body = issue.body if issue.body else ""
    raw_data: dict[str, Any] = extract_publish_info_from_issue(
        {
            "module_name": ADAPTER_MODULE_NAME_PATTERN,
            "project_link": PROJECT_LINK_PATTERN,
            "name": ADAPTER_NAME_PATTERN,
            "desc": ADAPTER_DESC_PATTERN,
            "homepage": ADAPTER_HOMEPAGE_PATTERN,
            "tags": TAGS_PATTERN,
        },
        body,
    )
    raw_data.update(AuthorInfo.from_issue(issue).model_dump())

    with plugin_config.input_config.adapter_path.open("r", encoding="utf-8") as f:
        previous_data: list[dict[str, str]] = json.load(f)

    return validate_info(PublishType.ADAPTER, raw_data, previous_data)


async def validate_bot_info_from_issue(issue: Issue) -> ValidationDict:
    """从议题中提取机器人信息"""
    body = issue.body if issue.body else ""
    raw_data: dict[str, Any] = extract_publish_info_from_issue(
        {
            "name": BOT_NAME_PATTERN,
            "desc": BOT_DESC_PATTERN,
            "homepage": BOT_HOMEPAGE_PATTERN,
            "tags": TAGS_PATTERN,
        },
        body,
    )

    raw_data.update(AuthorInfo.from_issue(issue).model_dump())

    with plugin_config.input_config.bot_path.open("r", encoding="utf-8") as f:
        previous_data: list[dict[str, str]] = json.load(f)

    return validate_info(PublishType.BOT, raw_data, previous_data)
