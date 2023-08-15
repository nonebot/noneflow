import re

# PyPI 格式
PYPI_PACKAGE_NAME_PATTERN = re.compile(
    r"^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$",
    re.IGNORECASE,
)
# import 包名格式
PYTHON_MODULE_NAME_REGEX = re.compile(
    r"^([A-Z]|[A-Z][A-Z0-9._-]*[A-Z0-9])$",
    re.IGNORECASE,
)

MAX_NAME_LENGTH = 50
"""名称最大长度"""

PLUGIN_VALID_TYPE = ["application", "library"]
"""插件类型当前只支持 application 和 library"""

# NoneBot Store
STORE_ADAPTERS_URL = "https://nonebot.dev/adapters.json"

# 发布信息的项
ADAPTER_INFO_FIELDS = [
    "module_name",
    "project_link",
    "name",
    "desc",
    "author",
    "homepage",
    "tags",
    "is_official",
]
BOT_INFO_FIELDS = [
    "name",
    "desc",
    "author",
    "homepage",
    "tags",
    "is_official",
]
PLUGIN_INFO_FIELDS_STORE = [
    "module_name",
    "project_link",
    "author",
    "tags",
    "is_official",
]
PLUGIN_INFO_FIELDS_REGISTRY = [
    "module_name",
    "project_link",
    "name",
    "desc",
    "author",
    "homepage",
    "tags",
    "is_official",
    "type",
    "supported_adapters",
]
