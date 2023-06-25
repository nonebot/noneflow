import json
from collections.abc import Iterable

import httpx

from .constants import (
    PLUGINS_PATH,
    PREVIOUS_RESULTS_PATH,
    RESULTS_PATH,
    STORE_PLUGINS_PATH,
)
from .models import PluginData, TestResult
from .utils import load_json
from .validation import validate_plugin


class StoreTest:
    """商店测试"""

    def __init__(
        self,
        offset: int = 0,
        limit: int = 1,
        force: bool = False,
    ) -> None:
        self._offset = offset
        self._limit = limit
        self._force = force

        # 获取所需的数据
        self._plugin_list = {
            f'{plugin["project_link"]}:{plugin["module_name"]}': plugin
            for plugin in load_json(STORE_PLUGINS_PATH)
        }
        self._previous_results: dict[str, TestResult] = load_json(PREVIOUS_RESULTS_PATH)

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

    def should_skip(self, key: str, plugin: PluginData) -> bool:
        """是否跳过测试"""
        # 如果强制测试，则不跳过
        if self._force:
            return False
        # 如果插件为最新版本，则跳过测试
        latest_version = self.get_latest_version(plugin["project_link"])
        if latest_version == self._previous_results.get(key, {}).get("version"):
            print(f"插件 {key} 为最新版本，跳过测试")
            return True
        return False

    def generate_plugin_list(self, results: Iterable[TestResult]):
        """生成插件列表"""
        plugins = []
        for result in results:
            # 如果插件验证失败，则不会有新结果，直接使用老结果
            new_plugin: PluginData = result["plugin"]["new"] or result["plugin"]["old"]  # type: ignore
            new_plugin["valid"] = result["results"]["validation"]
            new_plugin["time"] = result["time"]
            plugins.append(new_plugin)

        with open(PLUGINS_PATH, "w", encoding="utf8") as f:
            json.dump(plugins, f, indent=2, ensure_ascii=False)

    async def run(self):
        """测试商店内插件情况"""
        test_plugins = list(self._plugin_list.items())[self._offset :]

        new_results: dict[str, TestResult] = {}

        i = 1
        for key, plugin in test_plugins:
            if i > self._limit:
                print(f"已达到测试上限 {self._limit}，测试停止")
                break
            if key.startswith("git+http"):
                continue

            if self.should_skip(key, plugin):
                continue

            print(f"{i}/{self._limit} 正在测试插件 {key} ...")
            new_results[key] = await validate_plugin(key, plugin)

            i += 1

        results: dict[str, TestResult] = {}
        # 按照插件列表顺序输出
        for key in self._plugin_list:
            # 如果新的测试结果中有，则使用新的测试结果
            # 否则使用上次测试结果
            if key in new_results:
                results[key] = new_results[key]
            elif key in self._previous_results:
                results[key] = self._previous_results[key]

        with open(RESULTS_PATH, "w", encoding="utf8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        self.generate_plugin_list(results.values())
