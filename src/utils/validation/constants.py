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
