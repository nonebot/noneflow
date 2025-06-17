from githubkit.rest import Issue
from pydantic import BaseModel
from pydantic_core import PydanticCustomError

from src.plugins.github import plugin_config
from src.plugins.github.utils import extract_issue_info_from_issue
from src.providers.constants import BOT_KEY_TEMPLATE, PYPI_KEY_TEMPLATE
from src.providers.models import AuthorInfo
from src.providers.utils import load_json_from_file
from src.providers.validation.models import PublishType

from .constants import (
    REMOVE_BOT_HOMEPAGE_PATTERN,
    REMOVE_BOT_NAME_PATTERN,
    REMOVE_PLUGIN_IMPORT_NAME_PATTERN,
    REMOVE_PLUGIN_MODULE_NAME_PATTERN,
    REMOVE_PLUGIN_PROJECT_LINK_PATTERN,
)


def load_publish_data(publish_type: PublishType):
    """加载对应类型的文件数据"""
    match publish_type:
        case PublishType.ADAPTER:
            return {
                PYPI_KEY_TEMPLATE.format(
                    project_link=adapter["project_link"],
                    module_name=adapter["module_name"],
                ): adapter
                for adapter in load_json_from_file(
                    plugin_config.input_config.adapter_path
                )
            }
        case PublishType.BOT:
            return {
                BOT_KEY_TEMPLATE.format(
                    name=bot["name"],
                    homepage=bot["homepage"],
                ): bot
                for bot in load_json_from_file(plugin_config.input_config.bot_path)
            }
        case PublishType.PLUGIN:
            return {
                PYPI_KEY_TEMPLATE.format(
                    project_link=plugin["project_link"],
                    module_name=plugin["module_name"],
                ): plugin
                for plugin in load_json_from_file(
                    plugin_config.input_config.plugin_path
                )
            }
        case PublishType.DRIVER:
            raise ValueError("不支持的删除类型")


class RemoveInfo(BaseModel):
    publish_type: PublishType
    key: str
    name: str


async def validate_author_info(issue: Issue, publish_type: PublishType) -> RemoveInfo:
    """
    通过议题获取作者 ID，然后验证待删除的数据项是否属于该作者
    """

    body = issue.body if issue.body else ""
    author_id = AuthorInfo.from_issue(issue).author_id

    match publish_type:
        case PublishType.PLUGIN | PublishType.ADAPTER:
            raw_data = extract_issue_info_from_issue(
                {
                    "module_name": [
                        REMOVE_PLUGIN_MODULE_NAME_PATTERN,
                        REMOVE_PLUGIN_IMPORT_NAME_PATTERN,
                    ],
                    "project_link": REMOVE_PLUGIN_PROJECT_LINK_PATTERN,
                },
                body,
            )
            module_name = raw_data.get("module_name")
            project_link = raw_data.get("project_link")
            if module_name is None or project_link is None:
                raise PydanticCustomError(
                    "info_not_found", "未填写数据项或填写格式有误"
                )

            key = PYPI_KEY_TEMPLATE.format(
                project_link=project_link, module_name=module_name
            )
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
                    "info_not_found", "未填写数据项或填写格式有误"
                )

            key = BOT_KEY_TEMPLATE.format(name=name, homepage=homepage)
        case _:
            raise PydanticCustomError("not_support", "暂不支持的移除类型")

    data = load_publish_data(publish_type)

    if key not in data:
        raise PydanticCustomError("not_found", "不存在对应信息的包")

    remove_item = data[key]
    if remove_item.get("author_id") != author_id:
        raise PydanticCustomError("author_info", "作者信息验证不匹配")

    return RemoveInfo(
        publish_type=publish_type,
        name=remove_item.get("name") or remove_item.get("module_name") or "",
        key=key,
    )
