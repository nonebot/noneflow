""" 测试并验证插件 """
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from pydantic import ValidationError

from src.plugins.publish.validation import PluginPublishInfo
from src.utils.helper import strip_ansi
from src.utils.plugin_test import PluginTest

from .constants import PLUGIN_CONFIGS_URL
from .models import Metadata, PluginData


def get_configs() -> dict[str, list[str]]:
    """获取插件配置项"""

    resp = httpx.get(PLUGIN_CONFIGS_URL)
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception("获取插件配置项失败")


_CONFIGS = get_configs()


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


async def validate_metadata(
    result: bool, plugin: PluginData, metadata: Metadata | None
):
    """验证插件元数据"""
    project_link = plugin["project_link"]
    module_name = plugin["module_name"]
    print(f"正在验证插件 {project_link}:{module_name} ...")

    if not metadata:
        return {
            "valid": False,
            "raw": None,
            "data": None,
            "message": "缺少元数据",
        }

    name = metadata.get("name")
    desc = metadata.get("description")
    homepage = metadata.get("homepage")
    type = metadata.get("type")
    supported_adapters = metadata.get("supported_adapters")

    raw_data = {
        "module_name": module_name,
        "project_link": project_link,
        "name": name,
        "desc": desc,
        "author": plugin["author"],
        "homepage": homepage,
        "tags": json.dumps(plugin["tags"]),
        "plugin_test_result": result,
        "type": type,
        "supported_adapters": supported_adapters,
    }
    try:
        publish_info = PluginPublishInfo(**raw_data)
        return {
            "valid": True,
            "raw": raw_data,
            "data": publish_info.dict(exclude={"plugin_test_result"}),
            "message": "通过",
        }
    except ValidationError as e:
        return {
            "valid": False,
            "raw": raw_data,
            "data": None,
            "message": str(e),
        }


async def validate_plugin(key: str, plugin: PluginData):
    """验证插件"""
    project_link = plugin["project_link"]
    module_name = plugin["module_name"]

    plugin_config = "\n".join(_CONFIGS.get(key, []))
    test = PluginTest(project_link, module_name, plugin_config)

    # 将 GitHub Action 的输出文件重定向到测试文件夹内
    test.github_output_file = (test.path / "output.txt").resolve()
    test.github_step_summary_file = (test.path / "summary.txt").resolve()
    # 加载测试脚本需要从环境变量中获取 GitHub Action 的输出文件路径
    os.environ["GITHUB_OUTPUT"] = str(test.github_output_file)

    # 获取测试结果
    result, output = await test.run()
    metadata = extract_metadata(test.path)
    metadata_result = await validate_metadata(result, plugin, metadata)
    version = extract_version(test.path)

    # 测试完成后删除测试文件夹
    shutil.rmtree(test.path)

    return {
        "run": result,
        "output": output,
        "valid": metadata_result["valid"],
        "metadata": metadata,
        "validation_message": metadata_result["message"],
        "validation_raw_data": metadata_result["raw"],
        "previous": plugin,
        "current": metadata_result["data"],
        "time": datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S"),
        "version": version,
    }
