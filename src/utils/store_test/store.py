import httpx

from .constants import (
    ADAPTERS_PATH,
    BOTS_PATH,
    DRIVERS_PATH,
    PLUGIN_KEY_TEMPLATE,
    PLUGINS_PATH,
    PREVIOUS_PLUGINS_PATH,
    PREVIOUS_RESULTS_PATH,
    RESULTS_PATH,
    STORE_ADAPTERS_PATH,
    STORE_BOTS_PATH,
    STORE_DRIVERS_PATH,
    STORE_PLUGINS_PATH,
)
from .models import Plugin, StorePlugin, TestResult
from .utils import dump_json, load_json
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

        # NoneBot 仓库中的数据
        self._store_adapters = load_json(STORE_ADAPTERS_PATH)
        self._store_bots = load_json(STORE_BOTS_PATH)
        self._store_drivers = load_json(STORE_DRIVERS_PATH)
        self._store_plugins: dict[str, StorePlugin] = {
            PLUGIN_KEY_TEMPLATE.format(
                project_link=plugin["project_link"],
                module_name=plugin["module_name"],
            ): plugin
            for plugin in load_json(STORE_PLUGINS_PATH)
        }
        # 上次测试的结果
        self._previous_results: dict[str, TestResult] = load_json(PREVIOUS_RESULTS_PATH)
        self._previous_plugins: dict[str, Plugin] = {
            PLUGIN_KEY_TEMPLATE.format(
                project_link=plugin["project_link"],
                module_name=plugin["module_name"],
            ): plugin
            for plugin in load_json(PREVIOUS_PLUGINS_PATH)
        }

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

    def should_skip(self, key: str) -> bool:
        """是否跳过测试"""
        # 如果强制测试，则不跳过
        if self._force:
            return False

        # 如果插件不在上次测试的结果中，则不跳过
        previous_result = self._previous_results.get(key)
        previous_plugin = self._previous_plugins.get(key)
        if not previous_result or not previous_plugin:
            return False

        # 如果插件为最新版本，则跳过测试
        latest_version = self.get_latest_version(previous_plugin["project_link"])
        if latest_version == previous_result["version"]:
            print(f"插件 {key} 为最新版本（{latest_version}），跳过测试")
            return True
        return False

    def skip_plugin_test(self, key: str) -> bool:
        """是否跳过插件测试"""
        if key in self._previous_plugins:
            return self._previous_plugins[key].get("skip_test", False)
        return False

    async def run(
        self, key: str | None = None, config: str | None = None, data: str | None = None
    ):
        """测试商店内插件情况"""
        new_results: dict[str, TestResult] = {}
        new_plugins: dict[str, Plugin] = {}

        if key:
            if self.should_skip(key):
                return

            print(f"正在测试插件 {key} ...")
            new_results[key], new_plugin = await validate_plugin(
                self._store_plugins[key],
                config or "",
                self.skip_plugin_test(key),
                data,
            )
            if new_plugin:
                new_plugins[key] = new_plugin
        else:
            test_plugins = list(self._store_plugins.items())[self._offset :]
            plugin_configs = {
                key: self._previous_results.get(key, {})
                .get("inputs", {})
                .get("config", "")
                for key, _ in test_plugins
            }

            i = 1
            for key, plugin in test_plugins:
                if i > self._limit:
                    print(f"已达到测试上限 {self._limit}，测试停止")
                    break
                if key.startswith("git+http"):
                    continue

                if self.should_skip(key):
                    continue

                print(f"{i}/{self._limit} 正在测试插件 {key} ...")

                new_results[key], new_plugin = await validate_plugin(
                    plugin,
                    plugin_configs.get(key, ""),
                    self.skip_plugin_test(key),
                )
                if new_plugin:
                    new_plugins[key] = new_plugin

                i += 1

        results: dict[str, TestResult] = {}
        plugins: dict[str, Plugin] = {}
        # 按照插件列表顺序输出
        for key in self._store_plugins:
            # 更新测试结果
            # 如果新的测试结果中有，则使用新的测试结果
            # 否则使用上次测试结果
            if key in new_results:
                results[key] = new_results[key]
            elif key in self._previous_results:
                results[key] = self._previous_results[key]

            # 更新插件列表
            if key in new_plugins:
                plugins[key] = new_plugins[key]
            elif key in self._previous_plugins:
                plugins[key] = self._previous_plugins[key]

        # 保存测试结果与生成的列表
        dump_json(RESULTS_PATH, results)
        dump_json(ADAPTERS_PATH, self._store_adapters)
        dump_json(BOTS_PATH, self._store_bots)
        dump_json(DRIVERS_PATH, self._store_drivers)
        dump_json(PLUGINS_PATH, list(plugins.values()))
