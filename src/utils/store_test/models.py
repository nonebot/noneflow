from typing import Any, TypedDict


class PluginData(TypedDict):
    """NoneBot 商店插件数据"""

    module_name: str
    project_link: str
    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Any]
    is_official: bool
    type: str
    supported_adapters: list[str]


class Metadata(TypedDict):
    """插件元数据"""

    name: str
    description: str
    homepage: str
    type: str
    supported_adapters: list[str]


class ValidationResult(TypedDict):
    """验证结果"""

    valid: bool
    raw: dict[str, Any] | None
    data: PluginData | None
    message: str
