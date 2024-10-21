import click

from src.providers.constants import (
    REGISTRY_PLUGIN_CONFIG_URL,
    REGISTRY_PLUGINS_URL,
    REGISTRY_RESULTS_URL,
    STORE_ADAPTERS_URL,
    STORE_BOTS_URL,
    STORE_DRIVERS_URL,
    STORE_PLUGINS_URL,
)

from .constants import (
    ADAPTERS_PATH,
    BOTS_PATH,
    DRIVERS_PATH,
    PLUGIN_CONFIG_PATH,
    PLUGIN_KEY_TEMPLATE,
    PLUGINS_PATH,
    RESULTS_PATH,
)
from .models import Plugin, StorePlugin, TestResult
from .utils import dump_json, get_latest_version, load_json
from .validation import validate_plugin

print = click.echo


class StoreTest:
    """商店测试"""

    def __init__(self) -> None:
        self._store_adapters = load_json(STORE_ADAPTERS_URL)
        self._store_bots = load_json(STORE_BOTS_URL)
        self._store_drivers = load_json(STORE_DRIVERS_URL)
        self._store_plugins: dict[str, StorePlugin] = {
            PLUGIN_KEY_TEMPLATE.format(
                project_link=plugin["project_link"],
                module_name=plugin["module_name"],
            ): StorePlugin(**plugin)
            for plugin in load_json(STORE_PLUGINS_URL)
        }
        # 插件配置文件
        self._plugin_configs: dict[str, str] = load_json(REGISTRY_PLUGIN_CONFIG_URL)
        # 上次测试的结果
        self._previous_results: dict[str, TestResult] = {
            key: TestResult(**value)
            for key, value in load_json(REGISTRY_RESULTS_URL).items()
        }
        self._previous_plugins: dict[str, Plugin] = {
            PLUGIN_KEY_TEMPLATE.format(
                project_link=plugin["project_link"],
                module_name=plugin["module_name"],
            ): Plugin(**plugin)
            for plugin in load_json(REGISTRY_PLUGINS_URL)
        }

    def should_skip(self, key: str, force: bool = False) -> bool:
        """是否跳过测试"""
        if key.startswith("git+http"):
            click.echo(f"插件 {key} 为 Git 插件，无法测试，已跳过")
            return True

        # 如果强制测试，则不跳过
        if force:
            return False

        # 如果插件不在上次测试的结果中，则不跳过
        previous_result: TestResult | None = self._previous_results.get(key)
        previous_plugin: Plugin | None = self._previous_plugins.get(key)
        if previous_result is None or previous_plugin is None:
            return False

        # 如果插件为最新版本，则跳过测试
        try:
            latest_version = get_latest_version(previous_plugin.project_link)
        except ValueError as e:
            click.echo(f"插件 {key} 获取最新版本失败：{e}，跳过测试")
            return False
        if latest_version == previous_result.version:
            click.echo(f"插件 {key} 为最新版本（{latest_version}），跳过测试")
            return True
        return False

    def skip_plugin_test(self, key: str) -> bool:
        """是否跳过插件测试

        Args:
            key (str): 插件标识符
        """
        if key in self._previous_plugins:
            return self._previous_plugins[key].skip_test
        return False

    def read_plugin_config(self, key: str) -> str:
        """获取插件配置
        优先从配置文件中获取，若不存在则从上次测试结果获取

        Args:
            key (str): 插件标识符
        """
        if self._plugin_configs.get(key):
            return self._plugin_configs[key]
        elif self._previous_results.get(key):
            return self._previous_results[key].config
        return ""

    async def test_plugin(
        self, key: str, config: str | None = None, plugin_data: str | None = None
    ) -> tuple[TestResult, Plugin | None]:
        """测试插件

        Args:
            key (str): 插件标识符
            config (str | None): 插件配置，若为 None 则从上次测试结果中获取
            plugin_data (str | None): 插件数据，不为 None 时，直接使用该数据且跳过测试
        """
        plugin = self._store_plugins[key]

        # 假设传入了 config， 则需要更新 plugin_config 文件
        if config:
            self._plugin_configs[key] = config
        config = self.read_plugin_config(key)

        new_result, new_plugin = await validate_plugin(
            plugin=plugin,
            config=config,
            skip_test=self.skip_plugin_test(key),
            plugin_data=plugin_data,
            previous_plugin=self._previous_plugins.get(key),
        )
        return new_result, new_plugin

    async def test_plugins(self, limit: int, force: bool):
        """批量测试插件

        Args:
            limit (int): 至多有效测试插件数量
            force (bool): 是否强制测试
        """
        new_results: dict[str, TestResult] = {}
        new_plugins: dict[str, Plugin] = {}
        i = 1
        test_plugins = list(self._store_plugins.keys())

        for key in test_plugins:
            if i > limit:
                click.echo(f"已达到测试上限 {limit}，测试停止")
                break

            # 是否需要跳过测试
            if self.should_skip(key, force):
                continue

            async def worker():
                new_result, new_plugin = await self.test_plugin(key)
                new_results[key] = new_result
                if new_plugin:
                    new_plugins[key] = new_plugin

            try:
                click.echo(f"{i}/{limit} 正在测试插件 {key} ...")
                await worker()  # TODO: 修改为并行
                i += 1
            except Exception as err:
                click.echo(err)
                continue

        return new_results, new_plugins

    def merge_data(
        self, new_results: dict[str, TestResult], new_plugins: dict[str, Plugin]
    ):
        """
        合并新的插件测试数据与结果并储存到仓库中

        Args:
            new_results (dict[str, TestResult]): 新的插件测试结果
            new_plugins (dict[str, Plugin]): 新的插件数据
        """
        results: dict[str, TestResult] = {}
        plugins: dict[str, Plugin] = {}
        for key in self._store_plugins:
            if key in new_results:
                results[key] = new_results[key]
            elif key in self._previous_results:
                results[key] = self._previous_results[key]

            if key in new_plugins:
                plugins[key] = new_plugins[key]
            elif key in self._previous_plugins:
                plugins[key] = self._previous_plugins[key]

        return results, plugins

    def dump_data(self, results: dict[str, TestResult], plugins: list[Plugin]):
        """储存数据到仓库中"""
        dump_json(ADAPTERS_PATH, self._store_adapters)
        dump_json(BOTS_PATH, self._store_bots)
        dump_json(DRIVERS_PATH, self._store_drivers)
        dump_json(PLUGINS_PATH, plugins)
        dump_json(RESULTS_PATH, results)
        dump_json(PLUGIN_CONFIG_PATH, self._plugin_configs)

    async def run(self, limit: int, force: bool = False):
        """运行商店测试

        Args:
            limit (int): 至多有效测试插件数量
            force (bool): 是否强制测试，默认为 False
        """
        new_results, new_plugins = await self.test_plugins(limit, force)
        results, plugins = self.merge_data(new_results, new_plugins)
        self.dump_data(results, list(plugins.values()))

    async def run_single_plugin(
        self,
        key: str,
        force: bool = False,
        plugin_data: str | None = None,
        config: str | None = None,
    ):
        """
        运行单次插件测试，来自 trigger_registry_update

        Args:
            key (str): 插件标识符
            forece (bool): 是否强制测试，默认为 False
        """
        if self.should_skip(key, force):
            return

        new_plugin: Plugin | None = None

        try:
            new_result, new_plugin = await self.test_plugin(key, config, plugin_data)
        except Exception as err:
            click.echo(err)

        if new_plugin:
            results, plugins = self.merge_data({key: new_result}, {key: new_plugin})
        else:
            results, plugins = self.merge_data({}, {})
        self.dump_data(results, list(plugins.values()))
