""" 测试并验证插件 """
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import cast
from zoneinfo import ZoneInfo

from src.utils.plugin_test import PluginTest, strip_ansi
from src.utils.validation import PublishType, validate_info

from .models import Metadata, Plugin, StorePlugin, TestResult


def extract_metadata(path: Path) -> Metadata | None:
    """提取插件元数据"""
    with open(path / "output.txt", encoding="utf8") as f:
        output = f.read()
    match = re.search(r"METADATA<<EOF\s([\s\S]+?)\sEOF", output)
    if match:
        return json.loads(match.group(1))


def extract_version(path: Path) -> str | None:
    """提取插件版本"""
    with open(path / "output.txt", encoding="utf8") as f:
        output = f.read()
    match = re.search(r"version\s+:\s+(\S+)", strip_ansi(output))
    if match:
        return match.group(1).strip()


async def validate_plugin(
    plugin: StorePlugin,
    config: str,
    skip_test: bool,
    data: str | None = None,
    previous_plugin: Plugin | None = None,
) -> tuple[TestResult, Plugin | None]:
    """验证插件

    如果传入了 data 参数，则直接使用 data 作为插件数据，不进行测试

    返回测试结果与验证后的插件数据

    如果插件验证失败，返回的插件数据为 None
    """
    now_str = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    # 需要从商店插件数据中获取的信息
    project_link = plugin["project_link"]
    module_name = plugin["module_name"]
    is_official = plugin["is_official"]

    # 如果传递了 data 参数
    # 则直接使用 data 作为插件数据
    # 并且将 skip_test 设置为 True
    if data:
        # 无法获取到插件版本
        version = None
        # 因为跳过测试，测试结果无意义
        plugin_test_result = True
        plugin_test_output = "已跳过测试"
        # 提供了 data 参数，所以验证默认通过
        validation_result = True
        validation_output = None
        # 为插件数据添加上所需的信息
        new_plugin = json.loads(data)
        new_plugin["valid"] = True
        new_plugin["version"] = version
        new_plugin["time"] = now_str
        new_plugin["skip_test"] = True
        new_plugin = cast(Plugin, new_plugin)

        metadata = {
            "name": new_plugin.get("name"),
            "description": new_plugin.get("desc"),
            "homepage": new_plugin.get("homepage"),
            "type": new_plugin.get("type"),
            "supported_adapters": new_plugin.get("supported_adapters"),
        }
    else:
        test = PluginTest(project_link, module_name, config)

        # 将 GitHub Action 的输出文件重定向到测试文件夹内
        test.github_output_file = (test.path / "output.txt").resolve()
        test.github_step_summary_file = (test.path / "summary.txt").resolve()
        # 加载测试脚本需要从环境变量中获取 GitHub Action 的输出文件路径
        os.environ["GITHUB_OUTPUT"] = str(test.github_output_file)

        # 获取测试结果
        plugin_test_result, plugin_test_output = await test.run()

        metadata = extract_metadata(test.path)
        version = extract_version(test.path)

        # 测试并提取完数据后删除测试文件夹
        shutil.rmtree(test.path)

        # 当跳过测试的插件首次通过加载测试，则不再标记为跳过测试
        should_skip = False if plugin_test_result else skip_test

        raw_data = {
            "module_name": module_name,
            "project_link": project_link,
            "author": plugin["author"],
            "tags": json.dumps(plugin["tags"]),
            "skip_plugin_test": should_skip,
            "plugin_test_result": plugin_test_result,
            "plugin_test_output": "",
            "plugin_test_metadata": metadata,
            "previous_data": [],
        }

        if metadata:
            raw_data["name"] = metadata.get("name")
            raw_data["desc"] = metadata.get("description")
            raw_data["homepage"] = metadata.get("homepage")
            raw_data["type"] = metadata.get("type")
            raw_data["supported_adapters"] = metadata.get("supported_adapters")
        elif skip_test and previous_plugin:
            raw_data["name"] = previous_plugin.get("name")
            raw_data["desc"] = previous_plugin.get("desc")
            raw_data["homepage"] = previous_plugin.get("homepage")
            raw_data["type"] = previous_plugin.get("type")
            raw_data["supported_adapters"] = previous_plugin.get("supported_adapters")

        validation_info_result = validate_info(PublishType.PLUGIN, raw_data)

        if validation_info_result["valid"]:
            new_plugin = validation_info_result["data"]
            # 插件验证过程中无法获取是否是官方插件，因此需要从原始数据中获取
            new_plugin["is_official"] = is_official
            new_plugin["valid"] = validation_info_result["valid"]
            new_plugin["version"] = version
            new_plugin["time"] = now_str
            new_plugin["skip_test"] = should_skip
            new_plugin = cast(Plugin, new_plugin)
        else:
            new_plugin = None

        validation_result = validation_info_result["valid"]
        validation_output = (
            None
            if validation_info_result["valid"]
            else {
                "data": validation_info_result["data"],
                "errors": validation_info_result["errors"],
            }
        )

    result: TestResult = {
        "time": now_str,
        "version": version,
        "results": {
            "validation": validation_result,
            "load": plugin_test_result,
            "metadata": bool(metadata),
        },
        "inputs": {"config": config},
        "outputs": {
            "validation": validation_output,
            "load": plugin_test_output,
            "metadata": metadata,
        },
    }

    return result, new_plugin
