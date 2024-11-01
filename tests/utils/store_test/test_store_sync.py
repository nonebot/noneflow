import json
from pathlib import Path

from inline_snapshot import snapshot
from pytest_mock import MockerFixture
from respx import MockRouter


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
                "tags": [{"label": "sync", "color": "#ffffff"}],
                "is_official": False,
                "type": "library",
                "supported_adapters": None,
                "valid": True,
                "time": "2023-06-22 11:58:18",
                "version": "0.0.1",
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
                "time": "2023-06-22 12:10:18",
                "version": "0.0.1",
                "skip_test": False,
            },
        ]
    )
    assert load_json(mocked_store_data["results"]) == snapshot(
        {
            "nonebot-plugin-datastore:nonebot_plugin_datastore": {
                "time": "2023-06-26T22:08:18.945584+08:00",
                "config": "",
                "version": "1.0.0",
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
