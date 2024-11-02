import os

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
STORE_ADAPTERS_URL = f"{STORE_BASE_URL}/adapters.json"
STORE_BOTS_URL = f"{STORE_BASE_URL}/bots.json"
STORE_DRIVERS_URL = f"{STORE_BASE_URL}/drivers.json"
STORE_PLUGINS_URL = f"{STORE_BASE_URL}/plugins.json"
"""plugin_test.py 中也有一个常量，需要同时修改"""

# 商店测试镜像
# https://github.com/orgs/nonebot/packages/container/package/nonetest
DOCKER_IMAGES_VERSION = os.environ.get("DOCKER_IMAGES_VERSION") or "latest"
DOCKER_IMAGES = f"ghcr.io/nonebot/nonetest:{{}}-{DOCKER_IMAGES_VERSION}"
