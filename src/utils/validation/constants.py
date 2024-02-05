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
STORE_ADAPTERS_URL = (
    "https://raw.githubusercontent.com/nonebot/nonebot2/master/assets/adapters.json"
)

# Pydantic 错误信息翻译
MESSAGE_TRANSLATIONS = {
    "model_type": "值不是合法的字典",
    "list_type": "值不是合法的列表",
    "set_type": "值不是合法的集合",
    "json_type": "JSON 格式不合法",
    "missing": "字段不存在",
    "color_error": "颜色格式不正确",
    "string_too_long": "字符串长度不能超过 {max_length} 个字符",
    "too_long": "列表长度不能超过 {max_length} 个元素",
}
