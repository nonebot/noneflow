from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, TypeVar

from src.providers.constants import (
    BOT_KEY_TEMPLATE,
    PYPI_KEY_TEMPLATE,
    REGISTRY_ADAPTERS_URL,
    REGISTRY_BOTS_URL,
    REGISTRY_DRIVERS_URL,
    REGISTRY_PLUGIN_CONFIG_URL,
    REGISTRY_PLUGINS_URL,
    REGISTRY_RESULTS_URL,
    STORE_ADAPTERS_URL,
    STORE_BOTS_URL,
    STORE_DRIVERS_URL,
    STORE_PLUGINS_URL,
    TIME_ZONE,
)
from src.providers.logger import logger
from src.providers.models import (
    RegistryAdapter,
    RegistryBot,
    RegistryDriver,
    RegistryPlugin,
    StoreAdapter,
    StoreBot,
    StoreDriver,
    StorePlugin,
    StoreTestResult,
)
from src.providers.utils import (
    add_step_summary,
    dump_json,
    get_pypi_version,
    load_json_from_web,
)

from .constants import (
    ADAPTERS_PATH,
    BOTS_PATH,
    DRIVERS_PATH,
    PLUGIN_CONFIG_PATH,
    PLUGINS_PATH,
    RESULTS_PATH,
    TEST_DIR,
)
from .validation import validate_plugin

if TYPE_CHECKING:
    from src.providers.models import RegistryArtifactData

StoreModelT = TypeVar("StoreModelT")
RegistryModelT = TypeVar("RegistryModelT")


class StoreTest:
    """商店测试"""

    def __init__(self) -> None:
        # 商店数据
        self._store_adapters: dict[str, StoreAdapter] = {
            PYPI_KEY_TEMPLATE.format(
                project_link=adapter["project_link"],
                module_name=adapter["module_name"],
            ): StoreAdapter(**adapter)
            for adapter in load_json_from_web(STORE_ADAPTERS_URL)
        }
        self._store_bots: dict[str, StoreBot] = {
            BOT_KEY_TEMPLATE.format(
                name=bot["name"],
                homepage=bot["homepage"],
            ): StoreBot(**bot)
            for bot in load_json_from_web(STORE_BOTS_URL)
        }
        self._store_drivers: dict[str, StoreDriver] = {
            PYPI_KEY_TEMPLATE.format(
                project_link=driver["project_link"],
                module_name=driver["module_name"],
            ): StoreDriver(**driver)
            for driver in load_json_from_web(STORE_DRIVERS_URL)
        }
        self._store_plugins: dict[str, StorePlugin] = {
            PYPI_KEY_TEMPLATE.format(
                project_link=plugin["project_link"],
                module_name=plugin["module_name"],
            ): StorePlugin(**plugin)
            for plugin in load_json_from_web(STORE_PLUGINS_URL)
        }
        # 上次测试的结果
        self._previous_results: dict[str, StoreTestResult] = {
            key: StoreTestResult(**value)
            for key, value in load_json_from_web(REGISTRY_RESULTS_URL).items()
        }
        self._previous_adapters: dict[str, RegistryAdapter] = {
            PYPI_KEY_TEMPLATE.format(
                project_link=adapter["project_link"],
                module_name=adapter["module_name"],
            ): RegistryAdapter(**adapter)
            for adapter in load_json_from_web(REGISTRY_ADAPTERS_URL)
        }
        self._previous_bots: dict[str, RegistryBot] = {
            BOT_KEY_TEMPLATE.format(
                name=bot["name"],
                homepage=bot["homepage"],
            ): RegistryBot(**bot)
            for bot in load_json_from_web(url=REGISTRY_BOTS_URL)
        }
        self._previous_drivers: dict[str, RegistryDriver] = {
            PYPI_KEY_TEMPLATE.format(
                project_link=driver["project_link"],
                module_name=driver["module_name"],
            ): RegistryDriver(**driver)
            for driver in load_json_from_web(REGISTRY_DRIVERS_URL)
        }
        self._previous_plugins: dict[str, RegistryPlugin] = {
            PYPI_KEY_TEMPLATE.format(
                project_link=plugin["project_link"], module_name=plugin["module_name"]
            ): RegistryPlugin(**plugin)
            for plugin in load_json_from_web(REGISTRY_PLUGINS_URL)
        }
        # 插件配置文件
        self._plugin_configs: dict[str, str] = load_json_from_web(
            REGISTRY_PLUGIN_CONFIG_URL
        )

    def should_skip(self, key: str, force: bool = False) -> bool:
        """是否跳过测试"""
        if key.startswith("git+http"):
            logger.info(f"插件 {key} 为 Git 插件，无法测试，已跳过")
            return True

        # 如果强制测试，则不跳过
        if force:
            return False

        # 如果插件不在上次测试的结果中，则不跳过
        previous_result: StoreTestResult | None = self._previous_results.get(key)
        previous_plugin: RegistryPlugin | None = self._previous_plugins.get(key)
        if previous_result is None or previous_plugin is None:
            return False

        # 如果插件为最新版本，则跳过测试
        try:
            latest_version = get_pypi_version(previous_plugin.project_link)
        except ValueError as e:
            logger.warning(f"插件 {key} 获取最新版本失败：{e}，跳过测试")
            return True
        if latest_version == previous_result.version:
            logger.info(f"插件 {key} 为最新版本（{latest_version}），跳过测试")
            return True
        return False

    def get_plugins_sorted_by_test_time(self) -> list[str]:
        """获取按测试时间倒序排列的插件列表"""
        # 获取所有有测试结果的插件，按测试时间倒序排列
        plugins_with_time = []
        for key in self._store_plugins.keys():
            if key in self._previous_results:
                test_time = self._previous_results[key].time
                plugins_with_time.append((key, test_time))

        # 按时间倒序排列（最新的在前面）
        plugins_with_time.sort(key=lambda x: x[1], reverse=True)

        # 提取插件 key 列表
        sorted_plugins = [plugin[0] for plugin in plugins_with_time]

        # 将没有测试结果的插件添加到列表末尾
        untested_plugins = [
            key
            for key in self._store_plugins.keys()
            if key not in self._previous_results
        ]
        sorted_plugins.extend(untested_plugins)

        return sorted_plugins

    def read_plugin_config(self, key: str) -> str:
        """获取插件配置

        从配置文件中获取，若不存在则返回空字符串，并设置默认值

        Args:
            key (str): 插件标识符
        """
        if self._plugin_configs.get(key) is not None:
            return self._plugin_configs[key]
        self._plugin_configs[key] = ""
        return ""

    async def test_plugin(self, key: str) -> tuple[StoreTestResult, RegistryPlugin]:
        """测试插件

        Args:
            key (str): 插件标识符
            config (str | None): 插件配置，若为 None 则从上次测试结果中获取
            plugin_data (str): 插件数据，不为 None 时，直接使用该数据且跳过测试
        """
        plugin = self._store_plugins[key]
        config = self.read_plugin_config(key)
        new_result, new_plugin = await validate_plugin(
            store_plugin=plugin,
            config=config,
            previous_plugin=self._previous_plugins.get(key),
        )
        return new_result, new_plugin

    async def test_plugins(
        self, limit: int, offset: int, force: bool, recent: bool = False
    ):
        """批量测试插件

        Args:
            limit (int): 至多有效测试插件数量
            offset (int): 测试插件偏移量
            force (bool): 是否强制测试
            recent (bool): 是否按测试时间倒序排列，优先测试最近测试的插件，默认为 False
        """
        new_results: dict[str, StoreTestResult] = {}
        new_plugins: dict[str, RegistryPlugin] = {}
        i = 1

        # 根据 recent 参数决定插件测试顺序
        if recent:
            test_plugins = self.get_plugins_sorted_by_test_time()[offset:]
        else:
            test_plugins = list(self._store_plugins.keys())[offset:]

        for key in test_plugins:
            if i > limit:
                logger.info(f"已达到测试上限 {limit}，测试停止")
                break

            # 是否需要跳过测试
            if self.should_skip(key, force):
                continue

            async def worker():
                new_result, new_plugin = await self.test_plugin(key)
                new_results[key] = new_result
                new_plugins[key] = new_plugin

            try:
                logger.info(f"{i}/{limit} 正在测试插件 {key} ...")
                await worker()  # TODO: 修改为并行
                i += 1
            except Exception as err:
                logger.error(f"{err}")
                continue

        summary = self.generate_github_summary(new_results)
        add_step_summary(summary)
        return new_results, new_plugins

    def merge_plugin_data(
        self,
        new_results: dict[str, StoreTestResult],
        new_plugins: dict[str, RegistryPlugin],
    ):
        """
        合并新的插件测试数据与结果并储存到仓库中

        Args:
            new_results (dict[str, TestResult]): 新的插件测试结果
            new_plugins (dict[str, Plugin]): 新的插件数据
        """
        results: dict[str, StoreTestResult] = {}
        plugins: dict[str, RegistryPlugin] = {}
        for key in self._store_plugins:
            if key in new_results:
                results[key] = new_results[key]
            elif key in self._previous_results:
                results[key] = self._previous_results[key]

            if key in new_plugins:
                plugins[key] = new_plugins[key]
            elif key in self._previous_plugins:
                plugins[key] = self._previous_plugins[key]

        self._previous_results = results
        self._previous_plugins = plugins

    def dump_data(self):
        """储存数据到仓库中"""
        if not TEST_DIR.exists():
            TEST_DIR.mkdir()

        dump_json(ADAPTERS_PATH, list(self._previous_adapters.values()))
        dump_json(BOTS_PATH, list(self._previous_bots.values()))
        dump_json(DRIVERS_PATH, list(self._previous_drivers.values()))
        dump_json(PLUGINS_PATH, list(self._previous_plugins.values()))
        dump_json(RESULTS_PATH, self._previous_results)
        # 插件配置不需要压缩
        dump_json(PLUGIN_CONFIG_PATH, self._plugin_configs, False)

    async def run(
        self, limit: int, offset: int = 0, force: bool = False, recent: bool = False
    ):
        """运行商店测试

        Args:
            limit (int): 至多有效测试插件数量
            offset (int): 测试插件偏移量
            force (bool): 是否强制测试，默认为 False
            recent (bool): 是否按测试时间倒序排列，优先测试最近测试的插件，默认为 False
        """
        new_results, new_plugins = await self.test_plugins(limit, offset, force, recent)
        self.merge_plugin_data(new_results, new_plugins)
        await self.sync_store()
        self.dump_data()

    async def run_single_plugin(self, key: str, force: bool = False):
        """
        运行单次插件测试，手动指定 key 运行

        Args:
            key (str): 插件标识符
            force (bool): 是否强制测试，默认为 False
        """
        if self.should_skip(key, force):
            return

        new_plugin: RegistryPlugin | None = None
        new_result: StoreTestResult | None = None

        try:
            new_result, new_plugin = await self.test_plugin(key)
            self.merge_plugin_data({key: new_result}, {key: new_plugin})
        except Exception as err:
            logger.error(f"{err}")

        self.dump_data()

    async def registry_update(self, data: "RegistryArtifactData"):
        """商店更新

        直接利用 artifact 中的数据更新商店数据
        """
        key = data.registry.key
        match data.registry:
            case RegistryAdapter():
                if key not in self._previous_adapters:
                    self._previous_adapters[key] = data.registry
            case RegistryBot():
                if key not in self._previous_bots:
                    self._previous_bots[key] = data.registry
            case RegistryDriver():
                if key not in self._previous_drivers:
                    self._previous_drivers[key] = data.registry
            case RegistryPlugin():
                if key not in self._previous_plugins:
                    self._previous_plugins[key] = data.registry
                if key not in self._previous_results and data.store_test_result:
                    self._previous_results[key] = data.store_test_result
                    self._plugin_configs[key] = data.store_test_result.config

        self.dump_data()

    @staticmethod
    def _sync_registry_data(
        previous_data: dict[str, RegistryModelT],
        store_data: dict[str, StoreModelT],
        data_type: str,
        update_registry: Callable[[RegistryModelT, StoreModelT], RegistryModelT],
        create_registry: Callable[[StoreModelT], RegistryModelT],
    ) -> dict[str, RegistryModelT]:
        """以 nonebot2 仓库商店数据为准同步 registry 数据。"""
        synced_data: dict[str, RegistryModelT] = {}
        # 只遍历当前 store 中存在的 key，未写入 synced_data 的旧 key 会被清理。
        for key, store_item in store_data.items():
            try:
                if key in previous_data:
                    synced_item = update_registry(previous_data[key], store_item)
                else:
                    synced_item = create_registry(store_item)
            except Exception as e:
                logger.error(f"{data_type} {key} 同步商店数据失败：{e}")
                if key in previous_data:
                    synced_data[key] = previous_data[key]
                continue

            synced_data[key] = synced_item

        return synced_data

    @staticmethod
    def _create_plugin_registry(_: StorePlugin) -> RegistryPlugin:
        # TODO: 如果插件不存在，尝试重新测试获取相关信息验证
        raise NotImplementedError("插件需要重新测试")

    async def sync_store(self):
        """同步商店数据

        以商店数据为准，更新商店数据到仓库中，如果仓库中不存在则获取用户名后存储
        """
        self._previous_adapters = self._sync_registry_data(
            self._previous_adapters,
            self._store_adapters,
            "适配器",
            RegistryAdapter.update,
            StoreAdapter.to_registry,
        )
        self._previous_bots = self._sync_registry_data(
            self._previous_bots,
            self._store_bots,
            "机器人",
            RegistryBot.update,
            StoreBot.to_registry,
        )
        self._previous_drivers = self._sync_registry_data(
            self._previous_drivers,
            self._store_drivers,
            "驱动器",
            RegistryDriver.update,
            StoreDriver.to_registry,
        )
        self._previous_plugins = self._sync_registry_data(
            self._previous_plugins,
            self._store_plugins,
            "插件",
            RegistryPlugin.update,
            self._create_plugin_registry,
        )

        store_plugin_keys = set(self._store_plugins)
        # 插件被从 nonebot2 仓库移除后，registry results 中对应的测试结果
        # 也要删除，避免继续输出孤立的旧插件 key。
        self._previous_results = {
            key: result
            for key, result in self._previous_results.items()
            if key in store_plugin_keys
        }
        # 插件配置与测试结果一样跟随插件列表收敛。
        self._plugin_configs = {
            key: config
            for key, config in self._plugin_configs.items()
            if key in store_plugin_keys
        }

    def generate_github_summary(self, results: dict[str, StoreTestResult]):
        """生成 GitHub 摘要"""
        valid_plugins = [
            plugin_name
            for plugin_name, result in results.items()
            if sum(result.results.values()) == 3
        ]
        invalid_plugins = [
            plugin_name
            for plugin_name, _ in results.items()
            if plugin_name not in valid_plugins
        ]
        summary = f"""# 📃 商店测试结果

> 📅 {datetime.now(TIME_ZONE).strftime("%Y-%m-%d %H:%M:%S %Z")}
> ♻️ 共测试 {len(results)} 个插件
> ✅ 更新成功：{len(valid_plugins)} 个
> ❌ 更新失败：{len(invalid_plugins)} 个

## 通过测试插件列表

{"\n".join([f"- {name}" for name in valid_plugins])}

## 未通过测试插件列表

{"\n".join([f"- {name}" for name in invalid_plugins])}
"""
        return summary
