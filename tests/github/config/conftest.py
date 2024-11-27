from pathlib import Path

import pytest


@pytest.fixture
def mock_results(tmp_path: Path):
    from src.providers.utils import dump_json

    plugins_path = tmp_path / "plugins.json"
    results_path = tmp_path / "results.json"
    plugin_configs_path = tmp_path / "plugin_configs.json"

    plugins = [
        {
            "module_name": "nonebot_plugin_treehelp",
            "project_link": "nonebot-plugin-treehelp",
            "name": "帮助",
            "desc": "获取插件帮助信息",
            "author": "he0119",
            "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
            "tags": [{"label": "test", "color": "#ffffff"}],
            "is_official": False,
            "type": "application",
            "supported_adapters": None,
            "valid": False,
            "time": "2022-01-01T00:00:00Z",
            "version": "0.0.1",
            "skip_test": False,
        }
    ]
    results = {
        "nonebot-plugin-treehelp:nonebot_plugin_treehelp": {
            "time": "2022-01-01T00:00:00.420957+08:00",
            "config": "",
            "version": "0.0.1",
            "test_env": {"python==3.12": False},
            "results": {"validation": False, "load": True, "metadata": True},
            "outputs": {
                "validation": None,
                "load": "test_output",
                "metadata": {
                    "name": "帮助",
                    "desc": "获取插件帮助信息",
                    "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
                    "type": "application",
                    "supported_adapters": None,
                },
            },
        }
    }
    plugin_configs = {"nonebot-plugin-treehelp:nonebot_plugin_treehelp": ""}

    dump_json(plugins_path, plugins)
    dump_json(results_path, results)
    dump_json(plugin_configs_path, plugin_configs)

    return {
        "plugins": plugins_path,
        "results": results_path,
        "plugin_configs": plugin_configs_path,
    }
