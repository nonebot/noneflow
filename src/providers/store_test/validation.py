"""测试并验证插件"""

from typing import Any

import click

from src.providers.constants import DOCKER_IMAGES
from src.providers.docker_test import DockerPluginTest
from src.providers.models import Plugin, StorePlugin, StoreTestResult
from src.providers.validation import PublishType, validate_info
from src.providers.validation.models import PluginPublishInfo, ValidationDict
from src.providers.validation.utils import get_author_name

from .utils import get_latest_version, get_upload_time


async def validate_plugin(
    store_plugin: StorePlugin, config: str, previous_plugin: Plugin | None = None
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
    pypi_version = get_latest_version(project_link)
    pypi_time = get_upload_time(project_link)

    # 测试插件
    test_result = await DockerPluginTest(
        DOCKER_IMAGES, project_link, module_name, config
    ).run("3.12")

    # 获取测试结果
    click.echo(f"测试结果：{test_result}")
    plugin_test_load = test_result.load
    plugin_test_output = "\n".join(test_result.outputs)
    test_version = test_result.version
    test_env = test_result.test_env
    metadata = test_result.metadata

    if previous_plugin is None:
        # 使用商店插件数据作为新的插件数据
        raw_data = {
            "module_name": module_name,
            "project_link": project_link,
            "author_id": store_plugin.author_id,
            "tags": store_plugin.tags,
            "is_official": store_plugin.is_official,
        }
    else:
        # 将上次的插件数据作为新的插件数据
        raw_data: dict[str, Any] = previous_plugin.model_dump()

    # 当跳过测试的插件首次通过加载测试，则不再标记为跳过测试
    should_skip: bool = False if plugin_test_load else raw_data.get("skip_test", False)
    raw_data["skip_test"] = should_skip
    raw_data["load"] = plugin_test_load
    raw_data["test_output"] = plugin_test_output

    # 更新插件信息
    raw_data["metadata"] = bool(metadata)
    if metadata:
        raw_data.update(metadata.model_dump())

    # 通过 Github API 获取插件作者名称
    try:
        author_name = get_author_name(store_plugin.author_id)
    except Exception:
        # 若无法请求，试图从上次的插件数据中获取
        author_name = previous_plugin.author if previous_plugin else ""
    raw_data["author"] = author_name

    # 更新插件信息
    raw_data["version"] = test_version or pypi_version
    raw_data["time"] = pypi_time

    # 验证插件信息
    result: ValidationDict = validate_info(PublishType.PLUGIN, raw_data, [])

    if result.valid:
        assert isinstance(result.info, PluginPublishInfo)
        new_plugin = Plugin.from_publish_info(result.info)
    else:
        # 同步商店的数据，比如 author_id, tags 和 is_official
        data = raw_data
        data.update(
            {
                "author_id": store_plugin.author_id,
                "tags": store_plugin.tags,
                "is_official": store_plugin.is_official,
                "valid": result.valid,
            }
        )
        new_plugin = Plugin(**data)

    validation_result = result.valid
    validation_output = (
        None if result.valid else {"data": result.valid_data, "errors": result.errors}
    )

    test_result = StoreTestResult(
        version=test_version,
        results={
            "validation": validation_result,
            "load": plugin_test_load,
            "metadata": bool(metadata),
        },
        config=config,
        outputs={
            "validation": validation_output,
            "load": plugin_test_output,
            "metadata": metadata,
        },
        test_env={test_env: True},
    )

    return test_result, new_plugin
