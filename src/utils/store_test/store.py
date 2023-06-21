import json
from pathlib import Path
from typing import Any

import httpx

from src.utils.plugin_test import STORE_PLUGINS_URL

from .constants import RESULTS_URL
from .models import PluginData
from .validation import validate_plugin


class StoreTest:
    """商店测试"""

    def __init__(self, offset: int = 0, limit: int = 1) -> None:
        self._offset = offset
        self._limit = limit

        # 输出文件位置
        self._result_path = Path("plugin_test") / "results.json"
        if not self._result_path.exists():
            self._result_path.touch()

        # 获取所需的数据
        self._plugin_list = self.get_plugin_list()
        self._previous_results = self.get_previous_results()

    def get_previous_results(self) -> dict[str, dict[str, Any]]:
        """获取上次测试结果"""

        resp = httpx.get(RESULTS_URL)
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception("获取上次测试结果失败")

    def get_plugin_list(self) -> dict[str, PluginData]:
        """获取插件列表

        通过 package_name:module_name 获取插件信息
        """

        resp = httpx.get(STORE_PLUGINS_URL)
        if resp.status_code == 200:
            return {
                f'{plugin["project_link"]}:{plugin["module_name"]}': plugin
                for plugin in resp.json()
            }
        else:
            raise Exception("获取插件配置失败")

    @staticmethod
    def get_latest_version(project_link: str) -> str | None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
        }
        url = f"https://pypi.org/pypi/{project_link}/json"
        r = httpx.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()["info"]["version"]
        else:
            return None

    async def run(self):
        """测试商店内插件情况"""
        test_plugins = list(self._plugin_list.items())[self._offset :]

        new_results = {}

        i = 1
        for key, plugin in test_plugins:
            if i > self._limit:
                print(f"已达到测试上限 {self._limit}，测试停止")
                break
            if key.startswith("git+http"):
                continue

            # 如果插件为最新版本，则跳过测试
            latest_version = self.get_latest_version(plugin["project_link"])
            if latest_version == self._previous_results.get(key, {}).get("version"):
                print(f"插件 {key} 为最新版本，跳过测试")
                continue

            print(f"{i}/{self._limit} 正在测试插件 {key} ...")
            new_results[key] = await validate_plugin(key, plugin)

            i += 1

        results = {}
        # 按照插件列表顺序输出
        for key in self._plugin_list:
            # 如果新的测试结果中有，则使用新的测试结果
            # 否则使用上次测试结果
            if key in new_results:
                results[key] = new_results[key]
            elif key in self._previous_results:
                results[key] = self._previous_results[key]

        with open(self._result_path, "w", encoding="utf8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
