from typing import Any

from githubkit.rest import Issue
from pydantic import BaseModel
from pydantic_core import PydanticCustomError

from src.plugins.github import plugin_config
from src.plugins.github.models import AuthorInfo
from src.plugins.github.utils import extract_issue_info_from_issue, load_json
from src.providers.store_test.constants import BOT_KEY_TEMPLATE, PYPI_KEY_TEMPLATE
from src.providers.validation.models import PublishType

from .constants import (
    REMOVE_BOT_HOMEPAGE_PATTERN,
    REMOVE_BOT_NAME_PATTERN,
    REMOVE_HOMEPAGE_PATTERN,
    REMOVE_PLUGIN_MODULE_NAME_PATTERN,
    REMOVE_PLUGIN_PROJECT_LINK_PATTERN,
)


class RemoveInfo(BaseModel):
    publish_type: PublishType
    # 待删除的数据项
    item: dict[str, Any]
    name: str


async def validate_author_info(issue: Issue, type: PublishType) -> RemoveInfo:
    """
    根据主页链接与作者信息找到对应的包的信息
    """

    body = issue.body if issue.body else ""
    author_id = AuthorInfo.from_issue(issue).author_id

    match type:
        case PublishType.PLUGIN:
            raw_data = extract_issue_info_from_issue(
                {
                    "module_name": REMOVE_PLUGIN_MODULE_NAME_PATTERN,
                    "project_link": REMOVE_PLUGIN_PROJECT_LINK_PATTERN,
                },
                body,
            )
            module_name = raw_data.get("module_name")
            project_link = raw_data.get("project_link")
            if module_name is None or project_link is None:
                raise PydanticCustomError(
                    "info_not_found", "未填写数据项或填写信息有误"
                )
            plugin_data = {
                PYPI_KEY_TEMPLATE.format(
                    project_link=plugin["project_link"],
                    module_name=plugin["module_name"],
                ): plugin
                for plugin in load_json(plugin_config.input_config.plugin_path)
            }
            key = PYPI_KEY_TEMPLATE.format(
                project_link=project_link, module_name=module_name
            )
            if key not in plugin_data:
                raise PydanticCustomError("not_found", "没有包含对应信息的包")

            plugin = plugin_data[key]
            if plugin.get("author_id") == author_id:
                return RemoveInfo(
                    publish_type=PublishType.ADAPTER,
                    name=plugin.get("name") or plugin.get("project_link") or "",
                    item=plugin,
                )
            else:
                raise PydanticCustomError("author_info", "作者信息不匹配")
        case PublishType.BOT:
            raw_data = extract_issue_info_from_issue(
                {
                    "name": REMOVE_BOT_NAME_PATTERN,
                    "homepage": REMOVE_BOT_HOMEPAGE_PATTERN,
                },
                body,
            )
            name = raw_data.get("name")
            homepage = raw_data.get("homepage")

            if name is None or homepage is None:
                raise PydanticCustomError(
                    "info_not_found", "未填写数据项或填写信息有误"
                )

            bot_data = {
                BOT_KEY_TEMPLATE.format(name=bot["name"], homepage=bot["homepage"]): bot
                for bot in load_json(plugin_config.input_config.bot_path)
            }
            key = BOT_KEY_TEMPLATE.format(name=name, homepage=homepage)
            if key not in bot_data:
                raise PydanticCustomError("not_found", "没有包含对应信息的包")

            bot = bot_data[key]
            if bot.get("author_id") == author_id:
                return RemoveInfo(
                    publish_type=PublishType.BOT,
                    name=bot.get("name") or "",
                    item=bot,
                )
            else:
                raise PydanticCustomError("author_info", "作者信息不匹配")
        case PublishType.ADAPTER:
            homepage = extract_issue_info_from_issue(
                {"homepage": REMOVE_HOMEPAGE_PATTERN}, issue.body or ""
            ).get("homepage")

            if homepage is None:
                raise PydanticCustomError(
                    "info_not_found", "未填写数据项或填写信息有误"
                )

            adapter_data = {
                adapter.get("homepage"): adapter
                for adapter in load_json(plugin_config.input_config.plugin_path)
            }

            if homepage not in adapter_data:
                raise PydanticCustomError("not_found", "没有包含对应信息的包")

            adapter = adapter_data[homepage]
            if adapter.get("author_id") == author_id:
                return RemoveInfo(
                    publish_type=PublishType.ADAPTER,
                    name=adapter.get("name") or "",
                    item=adapter,
                )
            else:
                raise PydanticCustomError("author_info", "作者信息不匹配")
        case _:
            raise PydanticCustomError("not_support", "暂不支持的移除类型")
