"""测试并验证插件"""

from typing import Any

from src.providers.docker_test import DockerPluginTest
from src.providers.logger import logger
from src.providers.models import RegistryPlugin, StorePlugin, StoreTestResult
from src.providers.utils import get_author_name, get_pypi_upload_time
from src.providers.validation import (
    PluginPublishInfo,
    PublishType,
    ValidationDict,
    validate_info,
)


async def validate_plugin(
    store_plugin: StorePlugin,
    config: str,
    previous_plugin: RegistryPlugin | None = None,
):
    """验证插件

    如果 previous_plugin 为 None，说明是首次验证插件

    返回测试结果与验证后的插件数据

    如果插件验证失败，返回的插件数据为 None
    """
    # 需要从商店插件数据中获取的信息
    project_link = store_plugin.project_link
    module_name = store_plugin.module_name

    # 从 PyPI 获取信息
    pypi_time = get_pypi_upload_time(project_link)

    # 测试插件
    plugin_test_result = await DockerPluginTest(project_link, module_name, config).run(
        "3.12"
    )

    plugin_test_load = plugin_test_result.load
    plugin_test_output = plugin_test_result.output
    plugin_test_version = plugin_test_result.version
    plugin_test_env = plugin_test_result.test_env
    plugin_metadata = plugin_test_result.metadata

    # 输出插件测试相关信息
    logger.info(
        f"插件 {project_link}({plugin_test_version}) 加载{'成功' if plugin_test_load else '失败'} {'插件已尝试加载' if plugin_test_result.run else '插件并未开始运行'}"
    )
    logger.info(f"插件元数据：{plugin_metadata}")
    logger.info("插件测试输出：")
    logger.info(plugin_test_output)

    if previous_plugin is None:
        # 使用商店插件数据作为新的插件数据
        raw_data = store_plugin.model_dump()
    else:
        # 将上次的插件数据作为新的插件数据
        raw_data: dict[str, Any] = previous_plugin.model_dump()
        # 还需要同步商店中的数据，如 author_id, tags 和 is_official
        raw_data.update(
            {
                "author_id": store_plugin.author_id,
                "tags": store_plugin.tags,
                "is_official": store_plugin.is_official,
            }
        )

    # 当跳过测试的插件首次通过加载测试，则不再标记为跳过测试
    should_skip: bool = False if plugin_test_load else raw_data.get("skip_test", False)
    raw_data["skip_test"] = should_skip
    raw_data["load"] = plugin_test_load
    raw_data["test_output"] = plugin_test_output
    raw_data["version"] = plugin_test_version

    # 使用最新的插件元数据更新插件信息
    raw_data["metadata"] = bool(plugin_metadata)
    if plugin_metadata:
        raw_data.update(plugin_metadata)

    # 通过 Github API 获取插件作者名称
    try:
        author_name = get_author_name(store_plugin.author_id)
    except Exception:
        # 若无法请求，试图从上次的插件数据中获取
        author_name = previous_plugin.author if previous_plugin else ""
    raw_data["author"] = author_name

    # 更新插件信息
    raw_data["time"] = pypi_time

    # 验证插件信息
    result: ValidationDict = validate_info(PublishType.PLUGIN, raw_data, [])

    if result.valid:
        assert isinstance(result.info, PluginPublishInfo)
        new_plugin = RegistryPlugin.from_publish_info(result.info)
    else:
        # 如果验证失败则使用以前的数据
        data = previous_plugin.model_dump() if previous_plugin else {}
        data.update(result.valid_data)
        # 顺便更新作者名与验证结果
        data.update(
            {
                "author": author_name,
                "valid": result.valid,
            }
        )
        new_plugin = RegistryPlugin(**data)

    validation_result = result.valid
    validation_output = (
        None if result.valid else {"data": result.valid_data, "errors": result.errors}
    )

    test_result = StoreTestResult(
        version=plugin_test_version,
        results={
            "validation": validation_result,
            "load": plugin_test_load,
            "metadata": bool(plugin_metadata),
        },
        config=config,
        outputs={
            "validation": validation_output,
            "load": plugin_test_output,
            "metadata": plugin_metadata,
        },
        test_env={plugin_test_env: True},
    )

    return test_result, new_plugin
