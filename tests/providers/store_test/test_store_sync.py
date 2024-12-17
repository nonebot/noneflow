import json
from pathlib import Path

from inline_snapshot import snapshot
from pytest_mock import MockerFixture
from respx import MockRouter

from tests.conftest import PyPIProject


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


async def test_store_sync(
    mocked_store_data: dict[str, Path], mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """测试同步商店数据

    均增加一个 tag，以测试数据是否正确同步
    """
    from src.providers.store_test.store import StoreTest
    from src.providers.utils import get_pypi_data

    test = StoreTest()
    await test.run(0, 0, False)

    assert load_json(mocked_store_data["adapters"]) == snapshot(
        [
            {
                "module_name": "nonebot.adapters.onebot.v11",
                "project_link": "nonebot-adapter-onebot",
                "name": "OneBot V11",
                "desc": "OneBot V11 协议",
                "author": "yanyongyu",
                "homepage": "https://onebot.adapters.nonebot.dev/",
                "tags": [{"label": "sync", "color": "#ffffff"}],
                "is_official": True,
                "time": "2024-10-24T07:34:56.115315Z",
                "version": "2.4.6",
            },
            {
                "module_name": "nonebot.adapters.onebot.v12",
                "project_link": "nonebot-adapter-onebot",
                "name": "OneBot V12",
                "desc": "OneBot V12 协议",
                "author": "he0119",
                "homepage": "https://onebot.adapters.nonebot.dev/",
                "tags": [],
                "is_official": True,
                "time": "2024-10-24T07:34:56.115315Z",
                "version": "2.4.6",
            },
        ]
    )
    assert load_json(mocked_store_data["bots"]) == snapshot(
        [
            {
                "name": "CoolQBot",
                "desc": "基于 NoneBot2 的聊天机器人",
                "author": "he0119",
                "homepage": "https://github.com/he0119/CoolQBot",
                "tags": [{"label": "sync", "color": "#ffffff"}],
                "is_official": False,
            },
            {
                "name": "Github Bot",
                "desc": "在QQ获取/处理Github repo/pr/issue",
                "author": "BigOrangeQWQ",
                "homepage": "https://github.com/cscs181/QQ-GitHub-Bot",
                "tags": [],
                "is_official": False,
            },
        ]
    )
    assert load_json(mocked_store_data["drivers"]) == snapshot(
        [
            {
                "module_name": "~none",
                "project_link": "",
                "name": "None",
                "desc": "None 驱动器",
                "author": "yanyongyu",
                "homepage": "/docs/advanced/driver",
                "tags": [{"label": "sync", "color": "#ffffff"}],
                "is_official": True,
                "time": "2024-10-31T13:47:14.152851Z",
                "version": "2.4.0",
            },
            {
                "module_name": "~fastapi",
                "project_link": "nonebot2[fastapi]",
                "name": "FastAPI",
                "desc": "FastAPI 驱动器",
                "author": "yanyongyu",
                "homepage": "/docs/advanced/driver",
                "tags": [],
                "is_official": True,
                "time": "2024-10-31T13:47:14.152851Z",
                "version": "2.4.0",
            },
            {
                "module_name": "~quart",
                "project_link": "nonebot2[quart]",
                "name": "Quart",
                "desc": "Quart 驱动器",
                "author": "he0119",
                "homepage": "/docs/advanced/driver",
                "tags": [],
                "is_official": True,
                "time": "2024-10-31T13:47:14.152851Z",
                "version": "2.4.0",
            },
        ]
    )
    assert load_json(mocked_store_data["plugins"]) == snapshot(
        [
            {
                "module_name": "nonebot_plugin_datastore",
                "project_link": "nonebot-plugin-datastore",
                "name": "数据存储",
                "desc": "NoneBot 数据存储插件",
                "author": "he0119",
                "homepage": "https://github.com/he0119/nonebot-plugin-datastore",
                "tags": [{"label": "good first plugin", "color": "#ffffff"}],
                "is_official": False,
                "type": "library",
                "supported_adapters": None,
                "valid": True,
                "time": "2024-06-20T07:53:23.524486Z",
                "version": "1.3.0",
                "skip_test": False,
            },
            {
                "module_name": "nonebot_plugin_treehelp",
                "project_link": "nonebot-plugin-treehelp",
                "name": "帮助",
                "desc": "获取插件帮助信息",
                "author": "he0119",
                "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
                "tags": [],
                "is_official": False,
                "type": "application",
                "supported_adapters": None,
                "valid": True,
                "time": "2024-07-13T04:41:40.905441Z",
                "version": "0.5.0",
                "skip_test": False,
            },
        ]
    )
    assert load_json(mocked_store_data["results"]) == snapshot(
        {
            "nonebot-plugin-datastore:nonebot_plugin_datastore": {
                "time": "2023-06-26T22:08:18.945584+08:00",
                "config": "",
                "version": "1.3.0",
                "test_env": None,
                "results": {"validation": True, "load": True, "metadata": True},
                "outputs": {
                    "validation": None,
                    "load": "datastore",
                    "metadata": {
                        "name": "数据存储",
                        "description": "NoneBot 数据存储插件",
                        "usage": "请参考文档",
                        "type": "library",
                        "homepage": "https://github.com/he0119/nonebot-plugin-datastore",
                        "supported_adapters": None,
                    },
                },
            },
            "nonebot-plugin-treehelp:nonebot_plugin_treehelp": {
                "time": "2023-06-26T22:20:41.833311+08:00",
                "config": "",
                "version": "0.3.0",
                "test_env": None,
                "results": {"validation": True, "load": True, "metadata": True},
                "outputs": {
                    "validation": None,
                    "load": "treehelp",
                    "metadata": {
                        "name": "帮助",
                        "description": "获取插件帮助信息",
                        "usage": """\
获取插件列表
/help
获取插件树
/help -t
/help --tree
获取某个插件的帮助
/help 插件名
获取某个插件的树
/help --tree 插件名
""",
                        "type": "application",
                        "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
                        "supported_adapters": None,
                    },
                },
            },
        }
    )

    # 当 PyPI 版本更新时，商店数据也应该更新
    pypi_projects = [
        PyPIProject(
            url="nonebot2",
            name="nonebot2",
            version="2.4.1",
            upload_time_iso_8601="2024-11-31T13:47:14.152851Z",
        ),
        PyPIProject(
            url="nonebot-adapter-onebot",
            name="nonebot-adapter-onebot",
            version="2.4.7",
            upload_time_iso_8601="2024-11-24T07:34:56.115315Z",
        ),
    ]
    for project in pypi_projects:
        mocked_api.get(
            f"https://pypi.org/pypi/{project['url']}/json",
            name=f"pypi_{project['url']}",
        ).respond(
            json={
                "info": {"name": project["name"], "version": project["version"]},
                "urls": [{"upload_time_iso_8601": project["upload_time_iso_8601"]}],
            }
        )

    # 缓存了 PyPI 数据，需要清除缓存
    get_pypi_data.cache_clear()

    test = StoreTest()
    await test.run(0, 0, False)

    assert load_json(mocked_store_data["adapters"]) == snapshot(
        [
            {
                "module_name": "nonebot.adapters.onebot.v11",
                "project_link": "nonebot-adapter-onebot",
                "name": "OneBot V11",
                "desc": "OneBot V11 协议",
                "author": "yanyongyu",
                "homepage": "https://onebot.adapters.nonebot.dev/",
                "tags": [{"label": "sync", "color": "#ffffff"}],
                "is_official": True,
                "time": "2024-11-24T07:34:56.115315Z",
                "version": "2.4.7",
            },
            {
                "module_name": "nonebot.adapters.onebot.v12",
                "project_link": "nonebot-adapter-onebot",
                "name": "OneBot V12",
                "desc": "OneBot V12 协议",
                "author": "he0119",
                "homepage": "https://onebot.adapters.nonebot.dev/",
                "tags": [],
                "is_official": True,
                "time": "2024-11-24T07:34:56.115315Z",
                "version": "2.4.7",
            },
        ]
    )
    assert load_json(mocked_store_data["bots"]) == snapshot(
        [
            {
                "name": "CoolQBot",
                "desc": "基于 NoneBot2 的聊天机器人",
                "author": "he0119",
                "homepage": "https://github.com/he0119/CoolQBot",
                "tags": [{"label": "sync", "color": "#ffffff"}],
                "is_official": False,
            },
            {
                "name": "Github Bot",
                "desc": "在QQ获取/处理Github repo/pr/issue",
                "author": "BigOrangeQWQ",
                "homepage": "https://github.com/cscs181/QQ-GitHub-Bot",
                "tags": [],
                "is_official": False,
            },
        ]
    )
    assert load_json(mocked_store_data["drivers"]) == snapshot(
        [
            {
                "module_name": "~none",
                "project_link": "",
                "name": "None",
                "desc": "None 驱动器",
                "author": "yanyongyu",
                "homepage": "/docs/advanced/driver",
                "tags": [{"label": "sync", "color": "#ffffff"}],
                "is_official": True,
                "time": "2024-11-31T13:47:14.152851Z",
                "version": "2.4.1",
            },
            {
                "module_name": "~fastapi",
                "project_link": "nonebot2[fastapi]",
                "name": "FastAPI",
                "desc": "FastAPI 驱动器",
                "author": "yanyongyu",
                "homepage": "/docs/advanced/driver",
                "tags": [],
                "is_official": True,
                "time": "2024-11-31T13:47:14.152851Z",
                "version": "2.4.1",
            },
            {
                "module_name": "~quart",
                "project_link": "nonebot2[quart]",
                "name": "Quart",
                "desc": "Quart 驱动器",
                "author": "he0119",
                "homepage": "/docs/advanced/driver",
                "tags": [],
                "is_official": True,
                "time": "2024-11-31T13:47:14.152851Z",
                "version": "2.4.1",
            },
        ]
    )
    assert load_json(mocked_store_data["plugins"]) == snapshot(
        [
            {
                "module_name": "nonebot_plugin_datastore",
                "project_link": "nonebot-plugin-datastore",
                "name": "数据存储",
                "desc": "NoneBot 数据存储插件",
                "author": "he0119",
                "homepage": "https://github.com/he0119/nonebot-plugin-datastore",
                "tags": [{"label": "good first plugin", "color": "#ffffff"}],
                "is_official": False,
                "type": "library",
                "supported_adapters": None,
                "valid": True,
                "time": "2024-06-20T07:53:23.524486Z",
                "version": "1.3.0",
                "skip_test": False,
            },
            {
                "module_name": "nonebot_plugin_treehelp",
                "project_link": "nonebot-plugin-treehelp",
                "name": "帮助",
                "desc": "获取插件帮助信息",
                "author": "he0119",
                "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
                "tags": [],
                "is_official": False,
                "type": "application",
                "supported_adapters": None,
                "valid": True,
                "time": "2024-07-13T04:41:40.905441Z",
                "version": "0.5.0",
                "skip_test": False,
            },
        ]
    )
    assert load_json(mocked_store_data["results"]) == snapshot(
        {
            "nonebot-plugin-datastore:nonebot_plugin_datastore": {
                "time": "2023-06-26T22:08:18.945584+08:00",
                "config": "",
                "version": "1.3.0",
                "test_env": None,
                "results": {"validation": True, "load": True, "metadata": True},
                "outputs": {
                    "validation": None,
                    "load": "datastore",
                    "metadata": {
                        "name": "数据存储",
                        "description": "NoneBot 数据存储插件",
                        "usage": "请参考文档",
                        "type": "library",
                        "homepage": "https://github.com/he0119/nonebot-plugin-datastore",
                        "supported_adapters": None,
                    },
                },
            },
            "nonebot-plugin-treehelp:nonebot_plugin_treehelp": {
                "time": "2023-06-26T22:20:41.833311+08:00",
                "config": "",
                "version": "0.3.0",
                "test_env": None,
                "results": {"validation": True, "load": True, "metadata": True},
                "outputs": {
                    "validation": None,
                    "load": "treehelp",
                    "metadata": {
                        "name": "帮助",
                        "description": "获取插件帮助信息",
                        "usage": """\
获取插件列表
/help
获取插件树
/help -t
/help --tree
获取某个插件的帮助
/help 插件名
获取某个插件的树
/help --tree 插件名
""",
                        "type": "application",
                        "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
                        "supported_adapters": None,
                    },
                },
            },
        }
    )
