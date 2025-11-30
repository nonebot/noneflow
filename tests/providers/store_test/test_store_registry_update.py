"""测试 store.py 中的 registry_update 函数不同分支"""

from pathlib import Path

from pytest_mock import MockerFixture
from respx import MockRouter


async def test_registry_update_adapter(
    mocked_store_data: dict[str, Path], mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """测试 registry_update 函数处理 RegistryAdapter 的分支"""
    from src.providers.models import (
        Color,
        RegistryAdapter,
        RegistryArtifactData,
        StoreAdapter,
        Tag,
    )
    from src.providers.store_test.store import StoreTest

    test = StoreTest()

    # 创建一个新的适配器数据
    new_adapter = RegistryAdapter(
        module_name="nonebot.adapters.new",
        project_link="nonebot-adapter-new",
        name="New Adapter",
        desc="A new adapter",
        author="test_author",
        homepage="https://example.com",
        tags=[Tag(label="new", color=Color("#ffffff"))],
        is_official=False,
        time="2024-01-01T00:00:00Z",
        version="1.0.0",
    )

    store_adapter = StoreAdapter(
        module_name="nonebot.adapters.new",
        project_link="nonebot-adapter-new",
        name="New Adapter",
        desc="A new adapter",
        author_id=123,
        homepage="https://example.com",
        tags=[Tag(label="new", color=Color("#ffffff"))],
        is_official=False,
    )

    artifact_data = RegistryArtifactData(
        store=store_adapter,
        registry=new_adapter,
        store_test_result=None,
    )

    # 执行 registry_update
    await test.registry_update(artifact_data)

    # 验证适配器已添加
    assert new_adapter.key in test._previous_adapters
    assert test._previous_adapters[new_adapter.key] == new_adapter


async def test_registry_update_bot(
    mocked_store_data: dict[str, Path], mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """测试 registry_update 函数处理 RegistryBot 的分支"""
    from src.providers.models import (
        Color,
        RegistryArtifactData,
        RegistryBot,
        StoreBot,
        Tag,
    )
    from src.providers.store_test.store import StoreTest

    test = StoreTest()

    # 创建一个新的机器人数据
    new_bot = RegistryBot(
        name="New Bot",
        desc="A new bot",
        author="test_author",
        homepage="https://example.com/newbot",
        tags=[Tag(label="new", color=Color("#ffffff"))],
        is_official=False,
    )

    store_bot = StoreBot(
        name="New Bot",
        desc="A new bot",
        author_id=123,
        homepage="https://example.com/newbot",
        tags=[Tag(label="new", color=Color("#ffffff"))],
        is_official=False,
    )

    artifact_data = RegistryArtifactData(
        store=store_bot,
        registry=new_bot,
        store_test_result=None,
    )

    # 执行 registry_update
    await test.registry_update(artifact_data)

    # 验证机器人已添加
    assert new_bot.key in test._previous_bots
    assert test._previous_bots[new_bot.key] == new_bot


async def test_registry_update_driver(
    mocked_store_data: dict[str, Path], mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """测试 registry_update 函数处理 RegistryDriver 的分支"""
    from src.providers.models import (
        Color,
        RegistryArtifactData,
        RegistryDriver,
        StoreDriver,
        Tag,
    )
    from src.providers.store_test.store import StoreTest

    test = StoreTest()

    # 创建一个新的驱动器数据
    new_driver = RegistryDriver(
        module_name="~newdriver",
        project_link="nonebot2[newdriver]",
        name="New Driver",
        desc="A new driver",
        author="test_author",
        homepage="https://example.com/newdriver",
        tags=[Tag(label="new", color=Color("#ffffff"))],
        is_official=True,
        time="2024-01-01T00:00:00Z",
        version="1.0.0",
    )

    store_driver = StoreDriver(
        module_name="~newdriver",
        project_link="nonebot2[newdriver]",
        name="New Driver",
        desc="A new driver",
        author_id=123,
        homepage="https://example.com/newdriver",
        tags=[Tag(label="new", color=Color("#ffffff"))],
        is_official=True,
    )

    artifact_data = RegistryArtifactData(
        store=store_driver,
        registry=new_driver,
        store_test_result=None,
    )

    # 执行 registry_update
    await test.registry_update(artifact_data)

    # 验证驱动器已添加
    assert new_driver.key in test._previous_drivers
    assert test._previous_drivers[new_driver.key] == new_driver


async def test_registry_update_plugin_with_result(
    mocked_store_data: dict[str, Path], mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """测试 registry_update 函数处理带测试结果的 RegistryPlugin 的分支"""
    from src.providers.models import (
        Color,
        RegistryArtifactData,
        RegistryPlugin,
        StorePlugin,
        StoreTestResult,
        Tag,
    )
    from src.providers.store_test.store import StoreTest

    test = StoreTest()

    # 创建一个新的插件数据
    new_plugin = RegistryPlugin(
        module_name="nonebot_plugin_new",
        project_link="nonebot-plugin-new",
        name="New Plugin",
        desc="A new plugin",
        author="test_author",
        homepage="https://example.com/newplugin",
        tags=[Tag(label="new", color=Color("#ffffff"))],
        is_official=False,
        type="application",
        supported_adapters=None,
        valid=True,
        time="2024-01-01T00:00:00Z",
        version="1.0.0",
        skip_test=False,
    )

    store_plugin = StorePlugin(
        module_name="nonebot_plugin_new",
        project_link="nonebot-plugin-new",
        author_id=123,
        tags=[Tag(label="new", color=Color("#ffffff"))],
        is_official=False,
    )

    # 创建测试结果
    test_result = StoreTestResult(
        time="2024-01-01T00:00:00+08:00",
        config="TEST_CONFIG=value",
        version="1.0.0",
        test_env={"python==3.12": True},
        results={"validation": True, "load": True, "metadata": True},
        outputs={
            "validation": None,
            "load": "Plugin loaded successfully",
            "metadata": {
                "name": "New Plugin",
                "description": "A new plugin",
            },
        },
    )

    artifact_data = RegistryArtifactData(
        store=store_plugin,
        registry=new_plugin,
        store_test_result=test_result,
    )

    # 执行 registry_update
    await test.registry_update(artifact_data)

    # 验证插件已添加
    assert new_plugin.key in test._previous_plugins
    assert test._previous_plugins[new_plugin.key] == new_plugin

    # 验证测试结果已添加
    assert new_plugin.key in test._previous_results
    assert test._previous_results[new_plugin.key] == test_result

    # 验证配置已保存
    assert test._plugin_configs[new_plugin.key] == "TEST_CONFIG=value"


async def test_registry_update_existing_key_not_updated(
    mocked_store_data: dict[str, Path], mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """测试 registry_update 函数不会覆盖已存在的数据"""
    from src.providers.models import (
        Color,
        RegistryArtifactData,
        RegistryPlugin,
        StorePlugin,
        StoreTestResult,
        Tag,
    )
    from src.providers.store_test.store import StoreTest

    test = StoreTest()

    # 获取一个已存在的插件 key
    existing_key = next(iter(test._previous_plugins.keys()))
    existing_plugin = test._previous_plugins[existing_key]
    existing_result = test._previous_results.get(existing_key)

    # 尝试用新数据更新
    new_plugin = RegistryPlugin(
        module_name=existing_plugin.module_name,
        project_link=existing_plugin.project_link,
        name="Updated Name",
        desc="Updated desc",
        author="updated_author",
        homepage="https://updated.com",
        tags=[Tag(label="updated", color=Color("#000000"))],
        is_official=True,
        type="library",
        supported_adapters=["adapter1"],
        valid=True,
        time="2025-01-01T00:00:00Z",
        version="2.0.0",
        skip_test=True,
    )

    store_plugin = StorePlugin(
        module_name=existing_plugin.module_name,
        project_link=existing_plugin.project_link,
        author_id=456,
        tags=[Tag(label="updated", color=Color("#000000"))],
        is_official=True,
    )

    new_result = StoreTestResult(
        time="2025-01-01T00:00:00+08:00",
        config="NEW_CONFIG=value",
        version="2.0.0",
        test_env={"python==3.13": True},
        results={"validation": True, "load": True, "metadata": True},
        outputs={
            "validation": None,
            "load": "Updated load output",
            "metadata": {"name": "Updated"},
        },
    )

    artifact_data = RegistryArtifactData(
        store=store_plugin,
        registry=new_plugin,
        store_test_result=new_result,
    )

    # 执行 registry_update
    await test.registry_update(artifact_data)

    # 验证插件未被更新（因为 key 已存在）
    assert test._previous_plugins[existing_key] == existing_plugin
    assert test._previous_plugins[existing_key].name != "Updated Name"

    # 验证结果也未被更新（如果原来存在）
    if existing_result is not None:
        assert test._previous_results[existing_key] == existing_result
