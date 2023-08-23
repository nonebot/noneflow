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

STORE_DIR = Path("plugin_test") / "store"
""" 商店信息文件夹 """
STORE_ADAPTERS_PATH = STORE_DIR / "adapters.json"
""" 适配器列表文件路径 """
STORE_BOTS_PATH = STORE_DIR / "bots.json"
""" 机器人列表文件路径 """
STORE_DRIVERS_PATH = STORE_DIR / "drivers.json"
""" 驱动器列表文件路径 """
STORE_PLUGINS_PATH = STORE_DIR / "plugins.json"
""" 插件列表文件路径 """
PREVIOUS_RESULTS_PATH = STORE_DIR / "previous_results.json"
""" 上次测试生成的结果文件路径 """
PREVIOUS_PLUGINS_PATH = STORE_DIR / "previous_plugins.json"
""" 上次测试生成的插件列表文件路径 """
