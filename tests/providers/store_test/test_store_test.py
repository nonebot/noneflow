from pathlib import Path

import httpx
from inline_snapshot import snapshot
from pytest_mock import MockerFixture
from respx import MockRouter


async def test_store_test(
    mocked_store_data: dict[str, Path], mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """验证插件信息

    第一个插件因为版本号无变化跳过
    第二插件验证通过
    因为 limit=1 所以只测试了一个插件，第三个插件未测试
    """
    from src.providers.store_test.store import (
        RegistryPlugin,
        StorePlugin,
        StoreTest,
        StoreTestResult,
    )

    mocked_validate_plugin = mocker.patch(
        "src.providers.store_test.store.validate_plugin"
    )
    mocked_validate_plugin.return_value = (
        StoreTestResult(
            time="2023-08-28T00:00:00.000000+08:00",
            version="1.0.0",
            config="",
            results={"load": True, "metadata": True, "validation": True},
            outputs={
                "load": "output",
                "metadata": {
                    "name": "帮助",
                    "description": "获取插件帮助信息",
                    "usage": "获取插件列表\n/help\n获取插件树\n/help -t\n/help --tree\n获取某个插件的帮助\n/help 插件名\n获取某个插件的树\n/help --tree 插件名\n",
                    "type": "application",
                    "homepage": "https://nonebot.dev/",
                    "supported_adapters": None,
                },
                "validation": None,
            },
        ),
        RegistryPlugin(
            name="帮助",
            module_name="module_name",
            author="author",
            version="0.3.0",
            desc="获取插件帮助信息",
            homepage="https://nonebot.dev/",
            project_link="project_link",
            tags=[],
            supported_adapters=None,
            type="application",
            time="2023-08-28T00:00:00.000000+08:00",
            is_official=True,
            valid=True,
            skip_test=False,
        ),
    )

    test = StoreTest()
    await test.run(1, 0, False)

    mocked_validate_plugin.assert_called_once_with(
        store_plugin=StorePlugin(
            tags=[],
            module_name="nonebot_plugin_treehelp",
            project_link="nonebot-plugin-treehelp",
            author_id=1,
            is_official=False,
        ),
        previous_plugin=RegistryPlugin(
            tags=[],
            module_name="nonebot_plugin_treehelp",
            project_link="nonebot-plugin-treehelp",
            name="帮助",
            desc="获取插件帮助信息",
            author="he0119",
            homepage="https://github.com/he0119/nonebot-plugin-treehelp",
            is_official=False,
            type="application",
            supported_adapters=None,
            valid=True,
            time="2024-07-13T04:41:40.905441Z",
            version="0.5.0",
            skip_test=False,
        ),
        config="TEST_CONFIG=true",
    )
    assert mocked_api["pypi_nonebot-plugin-treehelp"].called
    assert mocked_api["pypi_nonebot-plugin-datastore"].called

    assert mocked_store_data["adapters"].read_text(encoding="utf-8") == snapshot(
        '[{"module_name":"nonebot.adapters.onebot.v11","project_link":"nonebot-adapter-onebot","name":"OneBot V11","desc":"OneBot V11 协议","author":"yanyongyu","homepage":"https://onebot.adapters.nonebot.dev/","tags":[{"label":"sync","color":"#ffffff"}],"is_official":true,"time":"2024-10-24T07:34:56.115315Z","version":"2.4.6"},{"module_name":"nonebot.adapters.onebot.v12","project_link":"nonebot-adapter-onebot","name":"OneBot V12","desc":"OneBot V12 协议","author":"he0119","homepage":"https://onebot.adapters.nonebot.dev/","tags":[],"is_official":true,"time":"2024-10-24T07:34:56.115315Z","version":"2.4.6"}]'
    )
    assert mocked_store_data["bots"].read_text(encoding="utf-8") == snapshot(
        '[{"name":"CoolQBot","desc":"基于 NoneBot2 的聊天机器人","author":"he0119","homepage":"https://github.com/he0119/CoolQBot","tags":[{"label":"sync","color":"#ffffff"}],"is_official":false},{"name":"Github Bot","desc":"在QQ获取/处理Github repo/pr/issue","author":"BigOrangeQWQ","homepage":"https://github.com/cscs181/QQ-GitHub-Bot","tags":[],"is_official":false}]'
    )
    assert mocked_store_data["drivers"].read_text(encoding="utf-8") == snapshot(
        '[{"module_name":"~none","project_link":"","name":"None","desc":"None 驱动器","author":"yanyongyu","homepage":"/docs/advanced/driver","tags":[{"label":"sync","color":"#ffffff"}],"is_official":true,"time":"2024-10-31T13:47:14.152851Z","version":"2.4.0"},{"module_name":"~fastapi","project_link":"nonebot2[fastapi]","name":"FastAPI","desc":"FastAPI 驱动器","author":"yanyongyu","homepage":"/docs/advanced/driver","tags":[],"is_official":true,"time":"2024-10-31T13:47:14.152851Z","version":"2.4.0"},{"module_name":"~quart","project_link":"nonebot2[quart]","name":"Quart","desc":"Quart 驱动器","author":"he0119","homepage":"/docs/advanced/driver","tags":[],"is_official":true,"time":"2024-10-31T13:47:14.152851Z","version":"2.4.0"}]'
    )
    assert mocked_store_data["plugins"].read_text(encoding="utf-8") == snapshot(
        '[{"module_name":"nonebot_plugin_datastore","project_link":"nonebot-plugin-datastore","name":"数据存储","desc":"NoneBot 数据存储插件","author":"he0119","homepage":"https://github.com/he0119/nonebot-plugin-datastore","tags":[{"label":"sync","color":"#ffffff"}],"is_official":false,"type":"library","supported_adapters":null,"valid":true,"time":"2024-06-20T07:53:23.524486Z","version":"1.3.0","skip_test":false},{"module_name":"nonebot_plugin_treehelp","project_link":"nonebot-plugin-treehelp","name":"帮助","desc":"获取插件帮助信息","author":"author","homepage":"https://nonebot.dev/","tags":[],"is_official":false,"type":"application","supported_adapters":null,"valid":true,"time":"2023-08-28T00:00:00.000000+08:00","version":"0.3.0","skip_test":false}]'
    )
    assert mocked_store_data["results"].read_text(encoding="utf-8") == snapshot(
        '{"nonebot-plugin-datastore:nonebot_plugin_datastore":{"time":"2023-06-26T22:08:18.945584+08:00","config":"","version":"1.3.0","test_env":null,"results":{"validation":true,"load":true,"metadata":true},"outputs":{"validation":null,"load":"datastore","metadata":{"name":"数据存储","description":"NoneBot 数据存储插件","usage":"请参考文档","type":"library","homepage":"https://github.com/he0119/nonebot-plugin-datastore","supported_adapters":null}}},"nonebot-plugin-treehelp:nonebot_plugin_treehelp":{"time":"2023-08-28T00:00:00.000000+08:00","config":"","version":"1.0.0","test_env":null,"results":{"load":true,"metadata":true,"validation":true},"outputs":{"load":"output","metadata":{"name":"帮助","description":"获取插件帮助信息","usage":"获取插件列表\\n/help\\n获取插件树\\n/help -t\\n/help --tree\\n获取某个插件的帮助\\n/help 插件名\\n获取某个插件的树\\n/help --tree 插件名\\n","type":"application","homepage":"https://nonebot.dev/","supported_adapters":null},"validation":null}}}'
    )
    assert mocked_store_data["plugin_configs"].read_text(encoding="utf-8") == snapshot(
        """\
{
  "nonebot-plugin-treehelp:nonebot_plugin_treehelp": "TEST_CONFIG=true",
  "nonebot-plugin-datastore:nonebot_plugin_datastore": ""
}\
"""
    )


async def test_store_test_with_key(
    mocked_store_data: dict[str, Path], mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """测试指定插件，因为版本更新正常测试"""
    from src.providers.store_test.store import RegistryPlugin, StorePlugin, StoreTest

    mocked_validate_plugin = mocker.patch(
        "src.providers.store_test.store.validate_plugin"
    )
    mocked_validate_plugin.return_value = ({}, {})

    test = StoreTest()
    await test.run_single_plugin(key="nonebot-plugin-treehelp:nonebot_plugin_treehelp")

    mocked_validate_plugin.assert_called_once_with(
        store_plugin=StorePlugin(
            tags=[],
            module_name="nonebot_plugin_treehelp",
            project_link="nonebot-plugin-treehelp",
            author_id=1,
            is_official=False,
        ),
        previous_plugin=RegistryPlugin(
            tags=[],
            module_name="nonebot_plugin_treehelp",
            project_link="nonebot-plugin-treehelp",
            name="帮助",
            desc="获取插件帮助信息",
            author="he0119",
            homepage="https://github.com/he0119/nonebot-plugin-treehelp",
            is_official=False,
            type="application",
            supported_adapters=None,
            valid=True,
            time="2024-07-13T04:41:40.905441Z",
            version="0.5.0",
            skip_test=False,
        ),
        config="TEST_CONFIG=true",
    )

    assert mocked_api["pypi_nonebot-plugin-treehelp"].called
    assert not mocked_api["pypi_nonebot-plugin-datastore"].called


async def test_store_test_with_key_skip(
    mocked_store_data: dict[str, Path], mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """测试指定插件，因为版本未更新跳过测试"""
    from src.providers.store_test.store import StoreTest

    mocked_validate_plugin = mocker.patch(
        "src.providers.store_test.store.validate_plugin"
    )

    test = StoreTest()
    await test.run_single_plugin(
        key="nonebot-plugin-datastore:nonebot_plugin_datastore"
    )

    mocked_validate_plugin.assert_not_called()
    assert not mocked_api["pypi_nonebot-plugin-treehelp"].called
    assert mocked_api["pypi_nonebot-plugin-datastore"].called


async def test_store_test_raise(
    mocked_store_data: dict[str, Path],
    mocked_api: MockRouter,
    mocker: MockerFixture,
    respx_mock: MockRouter,
):
    """测试插件，但是测试过程中报错

    第一个插件因为版本号无变化跳过
    第二个插件获取版本号超时跳过
    第三个插件测试中也报错

    最后数据没有变化
    """
    from src.providers.store_test.store import StorePlugin, StoreTest

    respx_mock.get(
        "https://pypi.org/pypi/nonebot-plugin-treehelp/json",
        name="pypi_nonebot-plugin-treehelp",
    ).side_effect = httpx.ConnectTimeout

    mocked_validate_plugin = mocker.patch(
        "src.providers.store_test.store.validate_plugin"
    )
    mocked_validate_plugin.side_effect = Exception

    test = StoreTest()
    await test.run(limit=1)

    mocked_validate_plugin.assert_has_calls(
        [
            mocker.call(
                store_plugin=StorePlugin(
                    module_name="nonebot_plugin_wordcloud",
                    project_link="nonebot-plugin-wordcloud",
                    author_id=1,
                    tags=[],
                    is_official=False,
                ),
                previous_plugin=None,
                config="",
            ),  # type: ignore
        ]
    )

    # 数据没有更新，只是被压缩
    assert mocked_store_data["adapters"].read_text(encoding="utf-8") == snapshot(
        '[{"module_name":"nonebot.adapters.onebot.v11","project_link":"nonebot-adapter-onebot","name":"OneBot V11","desc":"OneBot V11 协议","author":"yanyongyu","homepage":"https://onebot.adapters.nonebot.dev/","tags":[{"label":"sync","color":"#ffffff"}],"is_official":true,"time":"2024-10-24T07:34:56.115315Z","version":"2.4.6"},{"module_name":"nonebot.adapters.onebot.v12","project_link":"nonebot-adapter-onebot","name":"OneBot V12","desc":"OneBot V12 协议","author":"he0119","homepage":"https://onebot.adapters.nonebot.dev/","tags":[],"is_official":true,"time":"2024-10-24T07:34:56.115315Z","version":"2.4.6"}]'
    )
    assert mocked_store_data["bots"].read_text(encoding="utf-8") == snapshot(
        '[{"name":"CoolQBot","desc":"基于 NoneBot2 的聊天机器人","author":"he0119","homepage":"https://github.com/he0119/CoolQBot","tags":[{"label":"sync","color":"#ffffff"}],"is_official":false},{"name":"Github Bot","desc":"在QQ获取/处理Github repo/pr/issue","author":"BigOrangeQWQ","homepage":"https://github.com/cscs181/QQ-GitHub-Bot","tags":[],"is_official":false}]'
    )
    assert mocked_store_data["drivers"].read_text(encoding="utf-8") == snapshot(
        '[{"module_name":"~none","project_link":"","name":"None","desc":"None 驱动器","author":"yanyongyu","homepage":"/docs/advanced/driver","tags":[{"label":"sync","color":"#ffffff"}],"is_official":true,"time":"2024-10-31T13:47:14.152851Z","version":"2.4.0"},{"module_name":"~fastapi","project_link":"nonebot2[fastapi]","name":"FastAPI","desc":"FastAPI 驱动器","author":"yanyongyu","homepage":"/docs/advanced/driver","tags":[],"is_official":true,"time":"2024-10-31T13:47:14.152851Z","version":"2.4.0"},{"module_name":"~quart","project_link":"nonebot2[quart]","name":"Quart","desc":"Quart 驱动器","author":"he0119","homepage":"/docs/advanced/driver","tags":[],"is_official":true,"time":"2024-10-31T13:47:14.152851Z","version":"2.4.0"}]'
    )
    assert mocked_store_data["plugins"].read_text(encoding="utf-8") == snapshot(
        '[{"module_name":"nonebot_plugin_datastore","project_link":"nonebot-plugin-datastore","name":"数据存储","desc":"NoneBot 数据存储插件","author":"he0119","homepage":"https://github.com/he0119/nonebot-plugin-datastore","tags":[{"label":"sync","color":"#ffffff"}],"is_official":false,"type":"library","supported_adapters":null,"valid":true,"time":"2024-06-20T07:53:23.524486Z","version":"1.3.0","skip_test":false},{"module_name":"nonebot_plugin_treehelp","project_link":"nonebot-plugin-treehelp","name":"帮助","desc":"获取插件帮助信息","author":"he0119","homepage":"https://github.com/he0119/nonebot-plugin-treehelp","tags":[],"is_official":false,"type":"application","supported_adapters":null,"valid":true,"time":"2024-07-13T04:41:40.905441Z","version":"0.5.0","skip_test":false}]'
    )
    assert mocked_store_data["results"].read_text(encoding="utf-8") == snapshot(
        '{"nonebot-plugin-datastore:nonebot_plugin_datastore":{"time":"2023-06-26T22:08:18.945584+08:00","config":"","version":"1.3.0","test_env":null,"results":{"validation":true,"load":true,"metadata":true},"outputs":{"validation":null,"load":"datastore","metadata":{"name":"数据存储","description":"NoneBot 数据存储插件","usage":"请参考文档","type":"library","homepage":"https://github.com/he0119/nonebot-plugin-datastore","supported_adapters":null}}},"nonebot-plugin-treehelp:nonebot_plugin_treehelp":{"time":"2023-06-26T22:20:41.833311+08:00","config":"","version":"0.3.0","test_env":null,"results":{"validation":true,"load":true,"metadata":true},"outputs":{"validation":null,"load":"treehelp","metadata":{"name":"帮助","description":"获取插件帮助信息","usage":"获取插件列表\\n/help\\n获取插件树\\n/help -t\\n/help --tree\\n获取某个插件的帮助\\n/help 插件名\\n获取某个插件的树\\n/help --tree 插件名\\n","type":"application","homepage":"https://github.com/he0119/nonebot-plugin-treehelp","supported_adapters":null}}}}'
    )

    assert mocked_api["pypi_nonebot-plugin-datastore"].called
    assert mocked_api["pypi_nonebot-plugin-treehelp"].called
    # 因为没有之前测试的结果，所以不需要获取插件版本号，直接开始测试
    assert not mocked_api["pypi_nonebot-plugin-wordcloud"].called


async def test_store_test_with_recent_parameter(
    mocked_store_data: dict[str, Path], mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """测试 recent 参数，验证插件按测试时间倒序排列"""
    from src.providers.store_test.store import (
        RegistryPlugin,
        StorePlugin,
        StoreTest,
        StoreTestResult,
    )

    # Mock validate_plugin 返回结果
    mocked_validate_plugin = mocker.patch(
        "src.providers.store_test.store.validate_plugin"
    )
    mocked_validate_plugin.return_value = (
        StoreTestResult(
            time="2024-01-01T00:00:00.000000+08:00",
            version="1.0.0",
            config="",
            results={"load": True, "metadata": True, "validation": True},
            outputs={
                "load": "output",
                "metadata": {
                    "name": "测试插件",
                    "description": "测试插件描述",
                    "type": "application",
                    "homepage": "https://example.com/",
                    "supported_adapters": None,
                },
                "validation": None,
            },
        ),
        RegistryPlugin(
            name="测试插件",
            module_name="test_module",
            author="test_author",
            version="1.0.0",
            desc="测试插件描述",
            homepage="https://example.com/",
            project_link="test-plugin",
            tags=[],
            supported_adapters=None,
            type="application",
            time="2024-01-01T00:00:00.000000+08:00",
            is_official=False,
            valid=True,
            skip_test=False,
        ),
    )

    # Mock get_plugins_sorted_by_test_time 方法来验证调用
    test = StoreTest()
    mocked_get_sorted = mocker.patch.object(test, "get_plugins_sorted_by_test_time")

    # 设置预期的排序结果（按测试时间倒序）
    # nonebot-plugin-treehelp 的测试时间是 2024-07-13T04:41:40.905441Z
    # nonebot-plugin-datastore 的测试时间是 2023-06-26T22:08:18.945584+08:00
    # 所以 treehelp 应该排在前面
    mocked_get_sorted.return_value = [
        "nonebot-plugin-treehelp:nonebot_plugin_treehelp",
        "nonebot-plugin-datastore:nonebot_plugin_datastore",
        "nonebot-plugin-wordcloud:nonebot_plugin_wordcloud",  # 没有测试结果的插件
    ]

    # 使用 recent=True 参数运行测试
    await test.run(limit=1, offset=0, force=False, recent=True)

    # 验证 get_plugins_sorted_by_test_time 被调用
    mocked_get_sorted.assert_called_once()

    # 验证测试了第一个插件（最近测试的）
    mocked_validate_plugin.assert_called_once_with(
        store_plugin=StorePlugin(
            tags=[],
            module_name="nonebot_plugin_treehelp",
            project_link="nonebot-plugin-treehelp",
            author_id=1,
            is_official=False,
        ),
        previous_plugin=RegistryPlugin(
            tags=[],
            module_name="nonebot_plugin_treehelp",
            project_link="nonebot-plugin-treehelp",
            name="帮助",
            desc="获取插件帮助信息",
            author="he0119",
            homepage="https://github.com/he0119/nonebot-plugin-treehelp",
            is_official=False,
            type="application",
            supported_adapters=None,
            valid=True,
            time="2024-07-13T04:41:40.905441Z",
            version="0.5.0",
            skip_test=False,
        ),
        config="TEST_CONFIG=true",
    )


async def test_get_plugins_sorted_by_test_time(
    mocked_store_data: dict[str, Path], mocked_api: MockRouter
) -> None:
    """测试 get_plugins_sorted_by_test_time 方法的排序逻辑"""
    from src.providers.store_test.store import StoreTest

    test = StoreTest()
    sorted_plugins = test.get_plugins_sorted_by_test_time()

    # 验证插件是否按测试时间倒序排列
    # nonebot-plugin-treehelp 的测试时间是 2024-07-13T04:41:40.905441Z (更晚)
    # nonebot-plugin-datastore 的测试时间是 2023-06-26T22:08:18.945584+08:00 (更早)
    # nonebot-plugin-wordcloud 没有测试结果，应该在最后
    expected_order = [
        "nonebot-plugin-treehelp:nonebot_plugin_treehelp",
        "nonebot-plugin-datastore:nonebot_plugin_datastore",
        "nonebot-plugin-wordcloud:nonebot_plugin_wordcloud",
    ]

    assert sorted_plugins == expected_order


async def test_store_test_with_key_raise(
    mocked_store_data: dict[str, Path], mocked_api: MockRouter, mocker: MockerFixture
):
    """测试指定插件，但是测试过程中报错"""
    from src.providers.store_test.store import StorePlugin, StoreTest

    mocked_validate_plugin = mocker.patch(
        "src.providers.store_test.store.validate_plugin"
    )
    mocked_validate_plugin.side_effect = Exception

    test = StoreTest()
    await test.run_single_plugin(
        key="nonebot-plugin-wordcloud:nonebot_plugin_wordcloud"
    )

    mocked_validate_plugin.assert_called_once_with(
        store_plugin=StorePlugin(
            module_name="nonebot_plugin_wordcloud",
            project_link="nonebot-plugin-wordcloud",
            author_id=1,
            tags=[],
            is_official=False,
        ),
        previous_plugin=None,
        config="",
    )

    # 数据没有更新，只是被压缩
    assert mocked_store_data["adapters"].read_text(encoding="utf-8") == snapshot(
        '[{"module_name":"nonebot.adapters.onebot.v11","project_link":"nonebot-adapter-onebot","name":"OneBot V11","desc":"OneBot V11 协议","author":"yanyongyu","homepage":"https://onebot.adapters.nonebot.dev/","tags":[],"is_official":true,"time":"2024-10-24T07:34:56.115315Z","version":"2.4.6"}]'
    )
    assert mocked_store_data["bots"].read_text(encoding="utf-8") == snapshot(
        '[{"name":"CoolQBot","desc":"基于 NoneBot2 的聊天机器人","author":"he0119","homepage":"https://github.com/he0119/CoolQBot","tags":[],"is_official":false}]'
    )
    assert mocked_store_data["drivers"].read_text(encoding="utf-8") == snapshot(
        '[{"module_name":"~none","project_link":"","name":"None","desc":"None 驱动器","author":"yanyongyu","homepage":"/docs/advanced/driver","tags":[],"is_official":true,"time":"2024-10-31T13:47:14.152851Z","version":"2.4.0"},{"module_name":"~fastapi","project_link":"nonebot2[fastapi]","name":"FastAPI","desc":"FastAPI 驱动器","author":"yanyongyu","homepage":"/docs/advanced/driver","tags":[],"is_official":true,"time":"2024-10-31T13:47:14.152851Z","version":"2.4.0"}]'
    )
    assert mocked_store_data["plugins"].read_text(encoding="utf-8") == snapshot(
        '[{"module_name":"nonebot_plugin_datastore","project_link":"nonebot-plugin-datastore","name":"数据存储","desc":"NoneBot 数据存储插件","author":"he0119","homepage":"https://github.com/he0119/nonebot-plugin-datastore","tags":[],"is_official":false,"type":"library","supported_adapters":null,"valid":true,"time":"2024-06-20T07:53:23.524486Z","version":"1.3.0","skip_test":false},{"module_name":"nonebot_plugin_treehelp","project_link":"nonebot-plugin-treehelp","name":"帮助","desc":"获取插件帮助信息","author":"he0119","homepage":"https://github.com/he0119/nonebot-plugin-treehelp","tags":[],"is_official":false,"type":"application","supported_adapters":null,"valid":true,"time":"2024-07-13T04:41:40.905441Z","version":"0.5.0","skip_test":false}]'
    )
    assert mocked_store_data["results"].read_text(encoding="utf-8") == snapshot(
        '{"nonebot-plugin-datastore:nonebot_plugin_datastore":{"time":"2023-06-26T22:08:18.945584+08:00","config":"","version":"1.3.0","test_env":null,"results":{"validation":true,"load":true,"metadata":true},"outputs":{"validation":null,"load":"datastore","metadata":{"name":"数据存储","description":"NoneBot 数据存储插件","usage":"请参考文档","type":"library","homepage":"https://github.com/he0119/nonebot-plugin-datastore","supported_adapters":null}}},"nonebot-plugin-treehelp:nonebot_plugin_treehelp":{"time":"2023-06-26T22:20:41.833311+08:00","config":"","version":"0.3.0","test_env":null,"results":{"validation":true,"load":true,"metadata":true},"outputs":{"validation":null,"load":"treehelp","metadata":{"name":"帮助","description":"获取插件帮助信息","usage":"获取插件列表\\n/help\\n获取插件树\\n/help -t\\n/help --tree\\n获取某个插件的帮助\\n/help 插件名\\n获取某个插件的树\\n/help --tree 插件名\\n","type":"application","homepage":"https://github.com/he0119/nonebot-plugin-treehelp","supported_adapters":null}}}}'
    )
