from typing import TYPE_CHECKING, Any, Literal, TypedDict, cast

from src.utils.constants import (
    ADAPTER_INFO_FIELDS,
    BOT_INFO_FIELDS,
    PLUGIN_INFO_FIELDS_REGISTRY,
    PLUGIN_INFO_FIELDS_STORE,
)

from .models import PublishType
from .render import results_to_comment, results_to_registry
from .utils import check_url, loc_to_name, resolve_adapter_name

if TYPE_CHECKING:
    from pydantic import ValidationError
    from pydantic.error_wrappers import ErrorDict


class ValidationDict(TypedDict):
    """验证结果字典"""

    type: Literal["pass", "fail"]
    name: str
    msg: str
    hint: str


def TagsDataParser(data: dict[str, Any]) -> ValidationDict:
    tags = [f"{tag.label}-{tag.color}" for tag in data["tags"]]
    return ValidationDict(
        type="pass",
        name="tags",
        msg=f"标签: {', '.join(tags)}。",
        hint="",
    )


def HomepageDataParser(data: dict[str, Any]) -> ValidationDict:
    homepage = data["homepage"]
    return ValidationDict(
        type="pass",
        name="homepage",
        msg=f"""项目 <a href="{homepage}">主页</a> 返回状态码 {check_url(homepage)}。""",
        hint="",
    )


def ProjectLinkDataParser(data: dict[str, Any]) -> ValidationDict:
    project_link = data["project_link"]
    return ValidationDict(
        type="pass",
        name="project_link",
        msg=f"""项目 <a href="https://pypi.org/project/{project_link}/">{project_link}</a> 已发布至 PyPI。""",
        hint="",
    )


def PluginTestDataParser(data: dict[str, Any]) -> ValidationDict:
    github_repository = data["github_repository"]
    github_run_id = data["github_run_id"]
    skip_plugin_test = data["skip_plugin_test"]
    action_url = f"https://github.com/{github_repository}/actions/runs/{github_run_id}"
    if skip_plugin_test:
        return ValidationDict(
            type="pass",
            name="plugin_test_result",
            msg=f"""插件 <a href="{action_url}">加载测试</a> 已跳过。""",
            hint="",
        )
    return ValidationDict(
        type="pass",
        name="plugin_test_result",
        msg=f"""插件 <a href="{action_url}">加载测试</a> 通过。""",
        hint="",
    )


def PluginTypeDataParser(data: dict[str, Any]) -> ValidationDict:
    plugin_type = data["type"]
    return ValidationDict(
        type="pass",
        name="type",
        msg=f"""插件类型: {plugin_type}。""",
        hint="",
    )


def PluginSupportedAdaptersDataParser(data: dict[str, Any]) -> ValidationDict:
    supported_adapters = data["supported_adapters"]
    if supported_adapters:
        supported_adapters = {resolve_adapter_name(x) for x in supported_adapters}
    if supported_adapters:
        return ValidationDict(
            type="pass",
            name="supported_adapters",
            msg=f"""插件支持的适配器: {', '.join(supported_adapters)}。""",
            hint="",
        )
    return ValidationDict(
        type="pass",
        name="supported_adapters",
        msg=f"""插件支持的适配器: 所有。""",
        hint="",
    )


data_parser = {
    "tags": TagsDataParser,
    "homepage": HomepageDataParser,
    "project_link": ProjectLinkDataParser,
    "plugin_test_result": PluginTestDataParser,
    "type": PluginTypeDataParser,
    "supported_adapters": PluginSupportedAdaptersDataParser,
}


def TagsErrorParser(error: "ErrorDict") -> ValidationDict:
    if len(error["loc"]) == 3:
        number = cast(int, error["loc"][1]) + 1
        if error["type"] == "value_error.missing":
            return ValidationDict(
                type="fail",
                name="tag",
                msg=f"第 {number} 个标签缺少 {error['loc'][2]} 字段。",
                hint="请确保标签字段完整。",
            )
        else:
            assert "ctx" in error
            return ValidationDict(
                type="fail",
                name="tag",
                msg=f"第 {number} 个{error['ctx']['msg']}",
                hint=error["ctx"]["hint"],
            )
    if error["type"] == "value_error.missing":
        return MissingErrorParser(error)
    assert "ctx" in error
    return ValidationDict(
        type="fail",
        name="tags",
        msg=error["ctx"]["msg"],
        hint=error["ctx"]["hint"],
    )


def MissingErrorParser(error: "ErrorDict") -> ValidationDict:
    loc = cast(str, error["loc"][0])
    return ValidationDict(
        type="fail",
        name=loc,
        msg=f"{loc_to_name(loc)}: 无法匹配到数据。",
        hint="请确保填写该项目。",
    )


def DefaultErrorParser(error: "ErrorDict") -> ValidationDict:
    if "ctx" not in error:
        raise ValueError(f"无法解析的错误。{error}")
    loc = cast(str, error["loc"][0])
    return ValidationDict(
        type="fail",
        name=loc,
        msg=error["ctx"]["msg"],
        hint=error["ctx"]["hint"],
    )


error_parser = {
    "tags": TagsErrorParser,
}


class ValidationResult:
    """信息验证结果"""

    def __init__(
        self,
        publish_type: PublishType,
        data: dict[str, Any],
        fields_set: set,
        errors: "ValidationError | None",
    ):
        self.type = publish_type
        self.data = data
        self.fields_set = fields_set
        self.errors = errors

        self.results: list[ValidationDict] = []

        self._parse_error()
        self._parse_data()

    @property
    def is_valid(self) -> bool:
        """是否验证通过"""
        return self.errors is None

    def _parse_error(self) -> None:
        if self.errors is None:
            return
        for error in self.errors.errors():
            loc = cast(str, error["loc"][0])
            type = error["type"]
            # 需要特殊处理的项
            if loc in error_parser:
                self.results.append(error_parser[loc](error))
            # 缺少的项
            elif type.startswith("value_error.missing"):
                self.results.append(MissingErrorParser(error))
            # 可以直接获取错误数据的项
            else:
                self.results.append(DefaultErrorParser(error))

    def _parse_data(self) -> None:
        for field in self.data:
            if field in data_parser:
                self.results.append(data_parser[field](self.data))

    async def render_issue_comment(self, reuse: bool = False):
        return await results_to_comment(self, reuse=reuse)

    async def render_registry_message(self):
        return await results_to_registry(self)

    def dumps_store(self) -> dict[str, Any]:
        """输出符合商店的格式"""
        match self.type:
            case PublishType.ADAPTER:
                return {key: self.data[key] for key in ADAPTER_INFO_FIELDS}
            case PublishType.BOT:
                return {key: self.data[key] for key in BOT_INFO_FIELDS}
            case PublishType.PLUGIN:
                return {key: self.data[key] for key in PLUGIN_INFO_FIELDS_STORE}
            case _:
                raise ValueError(f"无法处理的类型 {self.type}")

    def dumps_registry(self) -> dict[str, Any]:
        """输出符合 registry 的格式"""
        match self.type:
            case PublishType.ADAPTER:
                return {key: self.data[key] for key in ADAPTER_INFO_FIELDS}
            case PublishType.BOT:
                return {key: self.data[key] for key in BOT_INFO_FIELDS}
            case PublishType.PLUGIN:
                return {key: self.data[key] for key in PLUGIN_INFO_FIELDS_REGISTRY}
            case _:
                raise ValueError(f"无法处理的类型 {self.type}")
