import contextvars
import re
from typing import Any

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
CUSTOM_MESSAGES = {
    "type_error.dict": "值不是合法的字典",
    "type_error.list": "值不是合法的列表",
    "type_error.set": "值不是合法的集合",
    "type_error.none.not_allowed": "值不能为 None",
    "value_error.json": "JSON 格式不合法",
    "value_error.missing": "字段不存在",
    "value_error.color": "颜色格式不正确",
    "value_error.any_str.max_length": "字符串长度不能超过 {limit_value} 个字符",
    "value_error.list.max_items": "列表长度不能超过 {limit_value} 个元素",
}

VALIDATION_CONTEXT = contextvars.ContextVar[dict[str, Any]]("validation_context")
"""验证上下文"""
