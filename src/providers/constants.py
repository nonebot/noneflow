import os
from zoneinfo import ZoneInfo

TIME_ZONE = ZoneInfo("Asia/Shanghai")
""" NoneFlow 统一的时区 """

BOT_KEY_TEMPLATE = "{name}:{homepage}"
""" 机器人键名模板 """

PYPI_KEY_TEMPLATE = "{project_link}:{module_name}"
""" 插件键名模板 """

# NoneBot 插件商店测试结果
# https://github.com/nonebot/registry/tree/results
REGISTRY_BASE_URL = (
    os.environ.get("REGISTRY_BASE_URL")
    or "https://raw.githubusercontent.com/nonebot/registry/results"
)
REGISTRY_RESULTS_URL = f"{REGISTRY_BASE_URL}/results.json"
REGISTRY_ADAPTERS_URL = f"{REGISTRY_BASE_URL}/adapters.json"
REGISTRY_BOTS_URL = f"{REGISTRY_BASE_URL}/bots.json"
REGISTRY_DRIVERS_URL = f"{REGISTRY_BASE_URL}/drivers.json"
REGISTRY_PLUGINS_URL = f"{REGISTRY_BASE_URL}/plugins.json"
REGISTRY_PLUGIN_CONFIG_URL = f"{REGISTRY_BASE_URL}/plugin_configs.json"

# NoneBot 插件商店
# https://github.com/nonebot/nonebot2/tree/master/assets
STORE_BASE_URL = (
    os.environ.get("STORE_BASE_URL")
    or "https://raw.githubusercontent.com/nonebot/nonebot2/master/assets"
)
STORE_ADAPTERS_URL = f"{STORE_BASE_URL}/adapters.json5"
STORE_BOTS_URL = f"{STORE_BASE_URL}/bots.json5"
STORE_DRIVERS_URL = f"{STORE_BASE_URL}/drivers.json5"
STORE_PLUGINS_URL = f"{STORE_BASE_URL}/plugins.json5"

# 商店测试镜像
# https://github.com/orgs/nonebot/packages/container/package/nonetest
DOCKER_IMAGES_VERSION = os.environ.get("DOCKER_IMAGES_VERSION") or "latest"
DOCKER_IMAGES = f"ghcr.io/nonebot/nonetest:{DOCKER_IMAGES_VERSION}"
DOCKER_BIND_RESULT_PATH = "/app/plugin_test/test_result.json"

PLUGIN_TEST_DIR = "./plugin_test"

# Artifact 相关常量
REGISTRY_DATA_NAME = "registry_data.json"
"""传递给 Registry 的数据文件名，会上传至 Artifact 存储"""
