from typing import Any, Literal, TypedDict


class StorePlugin(TypedDict):
    """NoneBot 仓库中的插件数据"""

    module_name: str
    project_link: str
    author: str
    tags: list[Any]
    is_official: bool


class Plugin(TypedDict):
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
    valid: bool
    time: str


class Metadata(TypedDict):
    """插件元数据"""

    name: str
    description: str
    homepage: str
    type: str
    supported_adapters: list[str]


class PluginValidation(TypedDict):
    """验证插件的结果与输出"""

    result: bool
    output: str
    plugin: Plugin | None


class TestResult(TypedDict):
    """测试结果"""

    time: str
    version: str | None
    results: dict[Literal["validation", "load", "metadata"], bool]
    inputs: dict[Literal["config"], str]
    outputs: dict[Literal["validation", "load", "metadata"], Any]
