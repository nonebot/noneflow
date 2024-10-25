"""测试并验证插件"""

import json
from typing import Any

import click

from src.providers.constants import DOCKER_IMAGES
from src.providers.docker_test import DockerPluginTest
from src.providers.validation import PublishType, validate_info
from src.providers.validation.models import ValidationDict
from src.providers.validation.utils import get_author_name

from .models import Metadata, Plugin, StorePlugin, TestResult
from .utils import get_latest_version, get_upload_time


async def validate_plugin(
    plugin: StorePlugin,
    config: str,
    skip_test: bool,
    plugin_data: str | None = None,
    previous_plugin: Plugin | None = None,
) -> tuple[TestResult, Plugin | None]:
    """验证插件

    如果传入了 plugin_data 参数，则直接使用 plugin_data 作为插件数据，不进行测试

    返回测试结果与验证后的插件数据

    如果插件验证失败，返回的插件数据为 None
    """
    # 需要从商店插件数据中获取的信息
    project_link = plugin.project_link
    module_name = plugin.module_name
    is_official = plugin.is_official

    # 从 PyPI 获取信息
    pypi_version = get_latest_version(project_link)
    pypi_time = get_upload_time(project_link)

    # 如果传递了 data 参数
    # 则直接使用 data 作为插件数据
    # 并且将 skip_test 设置为 True
    if plugin_data:
        # 跳过测试时无法获取到测试的版本
        test_version = None
        # 跳过测试时无法获取到测试的环境
        test_env = "skip_test"
        # 因为跳过测试，测试结果无意义
        plugin_test_load = True
        plugin_test_output = "已跳过测试"
        # 提供了 data 参数，所以验证默认通过
        validation_result = True
        validation_output = None
        # 为插件数据添加上所需的信息
        new_plugin = json.loads(plugin_data)
        new_plugin["valid"] = True
        new_plugin["version"] = pypi_version
        new_plugin["time"] = pypi_time
        new_plugin["skip_test"] = True
        new_plugin = Plugin(**new_plugin)

        metadata: Metadata | None = Metadata(
            name=new_plugin.name,
            desc=new_plugin.desc,
            homepage=new_plugin.homepage,
            type=new_plugin.type,
            supported_adapters=new_plugin.supported_adapters,
        )
    else:
        test_result = await DockerPluginTest(
            DOCKER_IMAGES, project_link, module_name, config
        ).run("3.12")
        # 获取测试结果
        click.echo(f"测试结果：{test_result}")

        plugin_test_output = test_result.outputs
        plugin_test_load = test_result.load
        test_version = test_result.version
        test_env = test_result.test_env
        metadata = test_result.metadata

        # 当跳过测试的插件首次通过加载测试，则不再标记为跳过测试
        should_skip: bool = False if plugin_test_load else skip_test

        # 通过 Github API 获取插件作者名称
        try:
            author_name = get_author_name(plugin.author_id)
        except Exception:
            # 若无法请求，试图从上次的插件数据中获取
            author_name = previous_plugin.author if previous_plugin else ""

        raw_data: dict[str, Any] = {
            "module_name": module_name,
            "project_link": project_link,
            "author": author_name,
            "author_id": plugin.author_id,
            "tags": plugin.tags,
            "load": plugin_test_load,
            "plugin_test_output": "",
            "metadata": metadata,
        }
        context = {"previous_data": [], "skip_plugin_test": should_skip}

        if metadata:
            raw_data.update(metadata.model_dump())
        elif skip_test and previous_plugin:
            # 将上次的插件数据作为新的插件数据
            raw_data.update(previous_plugin.model_dump())
            raw_data.update(previous_plugin.metadata().model_dump())

            # 部分字段需要重置
            raw_data["metadata"] = previous_plugin.metadata()
            raw_data["version"] = pypi_version
            raw_data["time"] = pypi_time

        validation_data: ValidationDict = validate_info(
            PublishType.PLUGIN, raw_data, context
        )

        new_data = {
            # 插件验证过程中无法获取是否是官方插件，因此需要从原始数据中获取
            "is_official": is_official,
            "valid": validation_data.valid,
            "version": test_version or pypi_version,
            "time": pypi_time,
            "skip_test": should_skip,
        }
        # 如果验证失败，则使用上次的插件数据
        if validation_data.valid:
            data = validation_data.valid_data
            data.update(new_data)
            new_plugin = Plugin(**data)
        elif previous_plugin:
            data = previous_plugin.model_dump()
            data.update(new_data)
            new_plugin = Plugin(**data)

        else:
            new_plugin = None

        validation_result = validation_data.valid
        validation_output = (
            None
            if validation_data.valid
            else {"data": validation_data.valid_data, "errors": validation_data.errors}
        )

    result = TestResult(
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

    return result, new_plugin
