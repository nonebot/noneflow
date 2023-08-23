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

from .models import Metadata, Plugin, PluginValidation, StorePlugin, TestResult


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


async def validate_plugin_info(
    result: bool, plugin: StorePlugin, metadata: Metadata | None
) -> PluginValidation:
    """验证插件数据"""
    project_link = plugin["project_link"]
    module_name = plugin["module_name"]
    print(f"正在验证插件 {project_link}:{module_name} ...")

    raw_data = {
        "module_name": module_name,
        "project_link": project_link,
        "author": plugin["author"],
        "tags": json.dumps(plugin["tags"]),
        "skip_plugin_test": False,
        "plugin_test_result": result,
        "plugin_test_output": "",
        "previous_data": [],
    }

    if metadata:
        raw_data["name"] = metadata.get("name")
        raw_data["desc"] = metadata.get("description")
        raw_data["homepage"] = metadata.get("homepage")
        raw_data["type"] = metadata.get("type")
        raw_data["supported_adapters"] = metadata.get("supported_adapters")
    else:
        raw_data["name"] = project_link

    validation_result = validate_info(PublishType.PLUGIN, raw_data)
    return {
        "result": validation_result["valid"],
        "output": {
            "data": validation_result["data"],
            "errors": validation_result["errors"],
        },
        "plugin": cast(Plugin, validation_result["data"])
        if validation_result["valid"]
        else None,
    }


async def validate_plugin(
    plugin: StorePlugin, config: str
) -> tuple[TestResult, Plugin | None]:
    """验证插件

    返回测试结果与验证后的插件数据

    如果插件验证失败，返回的插件数据为 None
    """
    now_str = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()

    # 需要从商店插件数据中获取的信息
    project_link = plugin["project_link"]
    module_name = plugin["module_name"]
    is_official = plugin["is_official"]

    test = PluginTest(project_link, module_name, config)

    # 将 GitHub Action 的输出文件重定向到测试文件夹内
    test.github_output_file = (test.path / "output.txt").resolve()
    test.github_step_summary_file = (test.path / "summary.txt").resolve()
    # 加载测试脚本需要从环境变量中获取 GitHub Action 的输出文件路径
    os.environ["GITHUB_OUTPUT"] = str(test.github_output_file)

    # 获取测试结果
    load_result, load_output = await test.run()

    metadata = extract_metadata(test.path)
    version = extract_version(test.path)

    # 测试并提取完数据后删除测试文件夹
    shutil.rmtree(test.path)

    validation = await validate_plugin_info(load_result, plugin, metadata)

    new_plugin = validation["plugin"]
    if new_plugin:
        # 插件验证过程中无法获取是否是官方插件，因此需要从原始数据中获取
        new_plugin["is_official"] = is_official
        new_plugin["valid"] = validation["result"]
        new_plugin["version"] = version
        new_plugin["time"] = now_str

    result: TestResult = {
        "time": now_str,
        "version": version,
        "results": {
            "validation": validation["result"],
            "load": load_result,
            "metadata": bool(metadata),
        },
        "inputs": {"config": config},
        "outputs": {
            "validation": validation["output"],
            "load": load_output,
            "metadata": metadata,
        },
    }

    return result, new_plugin
