from pathlib import Path

PLUGIN_KEY_TEMPLATE = "{project_link}:{module_name}"
""" 插件键名模板 """

TEST_DIR = Path("plugin_test")
""" 测试文件夹 """

if not TEST_DIR.exists():
    TEST_DIR.mkdir()

RESULTS_PATH = TEST_DIR / "results.json"
""" 测试结果保存路径 """

ADAPTERS_PATH = TEST_DIR / "adapters.json"
""" 生成的适配器列表保存路径 """

BOTS_PATH = TEST_DIR / "bots.json"
""" 生成的机器人列表保存路径 """

DRIVERS_PATH = TEST_DIR / "drivers.json"
""" 生成的驱动器列表保存路径 """

PLUGINS_PATH = TEST_DIR / "plugins.json"
""" 生成的插件列表保存路径 """

PLUGIN_CONFIG_PATH = TEST_DIR / "plugin_configs.json"
""" 生成的插件配置保存路径 """
