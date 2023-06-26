from pathlib import Path

STORE_DIR = Path("plugin_test") / "store"
""" 商店信息文件夹 """
STORE_PLUGINS_PATH = STORE_DIR / "plugins.json"
""" 插件列表文件路径 """
STORE_BOTS_PATH = STORE_DIR / "bots.json"
""" 机器人列表文件路径 """
STORE_ADAPTERS_PATH = STORE_DIR / "adapters.json"
""" 适配器列表文件路径 """
PREVIOUS_RESULTS_PATH = STORE_DIR / "results.json"
""" 上次测试结果文件路径 """
MOCK_PLUGINS_PATH = STORE_DIR / "mock_plugins.json"
""" 模拟插件列表文件路径 """
# 通过测试的插件一定是未重复的，所以用空列表来充当插件列表文件
if not MOCK_PLUGINS_PATH.exists():
    MOCK_PLUGINS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MOCK_PLUGINS_PATH, "w", encoding="utf8") as f:
        f.write("[]")

TEST_DIR = Path("plugin_test")
""" 测试文件夹 """
if not TEST_DIR.exists():
    TEST_DIR.mkdir()
RESULTS_PATH = TEST_DIR / "results.json"
""" 测试结果保存路径 """
PLUGINS_PATH = TEST_DIR / "plugins.json"
""" 生成的插件列表保存路径 """
