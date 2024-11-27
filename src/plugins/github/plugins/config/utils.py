from nonebot import logger

from src.providers.constants import PYPI_KEY_TEMPLATE
from src.providers.models import RegistryPlugin, StoreTestResult
from src.providers.utils import dump_json, load_json_from_file
from src.providers.validation import ValidationDict
from src.providers.validation.models import PluginPublishInfo


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
