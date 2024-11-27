from typing import Any

from nonebot import logger

from src.plugins.github.models import AuthorInfo
from src.plugins.github.models.issue import IssueHandler
from src.plugins.github.plugins.publish.constants import (
    PLUGIN_CONFIG_PATTERN,
    PLUGIN_MODULE_NAME_PATTERN,
    PROJECT_LINK_PATTERN,
)
from src.plugins.github.plugins.publish.render import render_summary
from src.plugins.github.plugins.publish.validation import add_step_summary, strip_ansi
from src.plugins.github.utils import extract_issue_info_from_issue
from src.providers.constants import PYPI_KEY_TEMPLATE
from src.providers.docker_test import DockerPluginTest, Metadata
from src.providers.models import RegistryPlugin, StoreTestResult
from src.providers.utils import dump_json, load_json_from_file
from src.providers.validation import PublishType, ValidationDict, validate_info
from src.providers.validation.models import PluginPublishInfo


async def validate_info_from_issue(handler: IssueHandler) -> ValidationDict:
    """从议题中获取插件信息，并且运行插件测试加载且获取插件元信息后进行验证"""
    body = handler.issue.body if handler.issue.body else ""

    # 从议题里提取插件所需信息
    raw_data: dict[str, Any] = extract_issue_info_from_issue(
        {
            "module_name": PLUGIN_MODULE_NAME_PATTERN,
            "project_link": PROJECT_LINK_PATTERN,
            "test_config": PLUGIN_CONFIG_PATTERN,
        },
        body,
    )
    # 从历史插件中获取标签
    previous_plugins: dict[str, RegistryPlugin] = {
        PYPI_KEY_TEMPLATE.format(
            project_link=plugin["project_link"], module_name=plugin["module_name"]
        ): RegistryPlugin(**plugin)
        for plugin in load_json_from_file("plugins.json")
    }
    raw_data["tags"] = previous_plugins[PYPI_KEY_TEMPLATE.format(**raw_data)].tags
    # 更新作者信息
    raw_data.update(AuthorInfo.from_issue(handler.issue).model_dump())

    module_name: str = raw_data.get("module_name", None)
    project_link: str = raw_data.get("project_link", None)
    test_config: str = raw_data.get("test_config", "")

    # 因为修改插件重新测试，所以上次的数据不需要加载，不然会报错重复
    previous_data = []

    # 修改插件配置肯定是为了通过插件测试，所以一定不跳过测试
    raw_data["skip_test"] = False

    # 运行插件测试
    test = DockerPluginTest(project_link, module_name, test_config)
    test_result = await test.run("3.12")

    # 去除颜色字符
    test_output = strip_ansi("\n".join(test_result.outputs))
    metadata = test_result.metadata
    if metadata:
        # 从插件测试结果中获得元数据
        raw_data.update(metadata)

    # 更新插件测试结果
    raw_data["version"] = test_result.version
    raw_data["load"] = test_result.load
    raw_data["test_output"] = test_output
    raw_data["metadata"] = bool(metadata)

    # 输出插件测试相关信息
    add_step_summary(await render_summary(test_result, test_output, project_link))
    logger.info(
        f"插件 {project_link}({test_result.version}) 插件加载{'成功' if test_result.load else '失败'} {'插件已尝试加载' if test_result.run else '插件并未开始运行'}"
    )
    logger.info(f"插件元数据：{metadata}")
    logger.info("插件测试输出：")
    for output in test_result.outputs:
        logger.info(output)

    # 验证插件相关信息
    result = validate_info(PublishType.PLUGIN, raw_data, previous_data)

    if not result.valid_data.get("metadata"):
        # 如果没有跳过测试且缺少插件元数据，则跳过元数据相关的错误
        # 因为这个时候这些项都会报错，错误在此时没有意义
        metadata_keys = Metadata.__annotations__.keys()
        # 如果是重复报错，error["loc"] 是 ()
        result.errors = [
            error
            for error in result.errors
            if error["loc"] == () or error["loc"][0] not in metadata_keys
        ]
        # 元数据缺失时，需要删除元数据相关的字段
        for key in metadata_keys:
            result.valid_data.pop(key, None)

    return result


def update_file(result: ValidationDict) -> None:
    """更新文件"""
    if not isinstance(result.info, PluginPublishInfo):
        raise ValueError("仅支持修改插件配置")

    logger.info("正在更新配置文件和最新测试结果")

    # 读取文件
    previous_plugins: dict[str, RegistryPlugin] = {
        PYPI_KEY_TEMPLATE.format(
            project_link=plugin["project_link"], module_name=plugin["module_name"]
        ): RegistryPlugin(**plugin)
        for plugin in load_json_from_file("plugins.json")
    }
    previous_results: dict[str, StoreTestResult] = {
        key: StoreTestResult(**value)
        for key, value in load_json_from_file("results.json").items()
    }
    plugin_configs: dict[str, str] = load_json_from_file("plugin_configs.json")

    # 更新信息
    plugin = RegistryPlugin.from_publish_info(result.info)
    previous_plugins[plugin.key] = plugin
    previous_results[plugin.key] = StoreTestResult.from_info(result.info)
    plugin_configs[plugin.key] = result.info.test_config

    dump_json("plugins.json", list(previous_plugins.values()))
    dump_json("results.json", previous_results)
    dump_json("plugin_configs.json", plugin_configs, False)

    logger.info("文件更新完成")
