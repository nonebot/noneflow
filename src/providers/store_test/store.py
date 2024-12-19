from datetime import datetime

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
    RegistryUpdatePayload,
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
)
from .validation import validate_plugin


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

    async def test_plugins(self, limit: int, offset: int, force: bool):
        """批量测试插件

        Args:
            limit (int): 至多有效测试插件数量
            offset (int): 测试插件偏移量
            force (bool): 是否强制测试
        """
        new_results: dict[str, StoreTestResult] = {}
        new_plugins: dict[str, RegistryPlugin] = {}
        i = 1
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
        dump_json(ADAPTERS_PATH, list(self._previous_adapters.values()))
        dump_json(BOTS_PATH, list(self._previous_bots.values()))
        dump_json(DRIVERS_PATH, list(self._previous_drivers.values()))
        dump_json(PLUGINS_PATH, list(self._previous_plugins.values()))
        dump_json(RESULTS_PATH, self._previous_results)
        # 插件配置不需要压缩
        dump_json(PLUGIN_CONFIG_PATH, self._plugin_configs, False)

    async def run(self, limit: int, offset: int = 0, force: bool = False):
        """运行商店测试

        Args:
            limit (int): 至多有效测试插件数量
            offset (int): 测试插件偏移量
            force (bool): 是否强制测试，默认为 False
        """
        new_results, new_plugins = await self.test_plugins(limit, offset, force)
        self.merge_plugin_data(new_results, new_plugins)
        await self.sync_store()
        self.dump_data()

    async def run_single_plugin(self, key: str, force: bool = False):
        """
        运行单次插件测试，手动指定 key 运行

        Args:
            key (str): 插件标识符
            forece (bool): 是否强制测试，默认为 False
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

    async def registry_update(self, payload: RegistryUpdatePayload):
        """商店更新

        直接利用 payload 中的数据更新商店数据
        """
        key = payload.registry.key
        match payload.registry:
            case RegistryAdapter():
                if key not in self._previous_adapters:
                    self._previous_adapters[key] = payload.registry
            case RegistryBot():
                if key not in self._previous_bots:
                    self._previous_bots[key] = payload.registry
            case RegistryDriver():
                if key not in self._previous_drivers:
                    self._previous_drivers[key] = payload.registry
            case RegistryPlugin():
                if key not in self._previous_plugins:
                    self._previous_plugins[key] = payload.registry
                if key not in self._previous_results and payload.result:
                    self._previous_results[key] = payload.result
                    self._plugin_configs[key] = payload.result.config

        self.dump_data()

    async def sync_store(self):
        """同步商店数据

        以商店数据为准，更新商店数据到仓库中，如果仓库中不存在则获取用户名后存储
        """
        for key in self._store_adapters:
            try:
                if key in self._previous_adapters:
                    new_adapter = self._previous_adapters[key].update(
                        self._store_adapters[key]
                    )
                else:
                    new_adapter = self._store_adapters[key].to_registry()
            except Exception as e:
                logger.error(f"适配器 {key} 同步商店数据失败：{e}")
                continue
            self._previous_adapters[key] = new_adapter
        for key in self._store_bots:
            try:
                if key in self._previous_bots:
                    new_bot = self._previous_bots[key].update(self._store_bots[key])
                else:
                    new_bot = self._store_bots[key].to_registry()
            except Exception as e:
                logger.error(f"机器人 {key} 同步商店数据失败：{e}")
                continue

            self._previous_bots[key] = new_bot
        for key in self._store_drivers:
            try:
                if key in self._previous_drivers:
                    new_driver = self._previous_drivers[key].update(
                        self._store_drivers[key]
                    )
                else:
                    new_driver = self._store_drivers[key].to_registry()
            except Exception as e:
                logger.error(f"驱动器 {key} 同步商店数据失败：{e}")
                continue

            self._previous_drivers[key] = new_driver
        for key in self._store_plugins:
            try:
                if key in self._previous_plugins:
                    new_plugin = self._previous_plugins[key].update(
                        self._store_plugins[key]
                    )
                else:
                    # TODO: 如果插件不存在，尝试重新测试获取相关信息验证
                    raise NotImplementedError("插件需要重新测试")
            except Exception as e:
                logger.error(f"插件 {key} 同步商店数据失败：{e}")
                continue

            self._previous_plugins[key] = new_plugin

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

{'\n'.join([f'- {name}' for name in valid_plugins])}

## 未通过测试插件列表

{'\n'.join([f'- {name}' for name in invalid_plugins])}
"""
        return summary
