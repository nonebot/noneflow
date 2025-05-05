# ruff: noqa: UP040
import abc
from enum import Enum
from typing import Annotated, Any, TypeAlias

from pydantic import (
    BaseModel,
    Field,
    SkipValidation,
    StringConstraints,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic_core import ErrorDetails, PydanticCustomError, to_jsonable_python
from pydantic_extra_types.color import Color
from pyjson5 import Json5DecoderException

from src.providers.utils import (
    get_pypi_name,
    get_pypi_upload_time,
    get_pypi_version,
    load_json,
)

from .constants import (
    NAME_MAX_LENGTH,
    PLUGIN_VALID_TYPE,
    PYPI_PACKAGE_NAME_PATTERN,
    PYTHON_MODULE_NAME_REGEX,
)
from .utils import (
    check_pypi,
    check_url,
    get_adapters,
    resolve_adapter_name,
)


class PublishType(Enum):
    """发布的类型

    值为标签名
    """

    BOT = "Bot"
    PLUGIN = "Plugin"
    ADAPTER = "Adapter"
    DRIVER = "Driver"

    def __str__(self) -> str:
        return self.value


class Tag(BaseModel):
    """标签"""

    label: str = Field(max_length=10)
    color: Color

    @field_validator("label", mode="before")
    @classmethod
    def label_validator(cls, v: str):
        return v.removeprefix("t:")

    @field_serializer("color")
    def color_serializer(self, color: Color):
        return color.as_hex(format="long")

    @property
    def color_hex(self) -> str:
        return self.color.as_hex(format="long")


class PyPIMixin(BaseModel):
    module_name: str
    project_link: str

    time: str
    """上传时间

    从 PyPI 获取最新版本的上传时间
    """
    version: str
    """版本号

    从 PyPI 获取最新版本号或者由插件测试提供
    """

    @field_validator("module_name", mode="before")
    @classmethod
    def module_name_validator(cls, v: str) -> str:
        # NoneBot 内置驱动器都是以 ~ 开头的
        if issubclass(cls, DriverPublishInfo) and v.startswith("~"):
            return v

        if not PYTHON_MODULE_NAME_REGEX.match(v):
            raise PydanticCustomError("module_name", "包名不符合规范")
        return v

    @field_validator("project_link", mode="before")
    @classmethod
    def project_link_validator(cls, v: str) -> str:
        # NoneBot 内置驱动器需要特殊处理
        if issubclass(cls, DriverPublishInfo) and (
            v == "" or v.startswith("nonebot2[")
        ):
            return v

        if not PYPI_PACKAGE_NAME_PATTERN.match(v):
            raise PydanticCustomError("project_link.name", "PyPI 项目名不符合规范")

        if v and not check_pypi(v):
            raise PydanticCustomError("project_link.not_found", "PyPI 项目名不存在")

        # 使用 PyPI 提供的标准项目名
        v = get_pypi_name(v)
        return v

    @model_validator(mode="before")
    @classmethod
    def prevent_duplication(
        cls, values: dict[str, Any], info: ValidationInfo
    ) -> dict[str, Any]:
        module_name = values.get("module_name")
        project_link = values.get("project_link")

        context = info.context
        if context is None:  # pragma: no cover
            raise PydanticCustomError("validation_context", "未获取到验证上下文")
        data = context.get("previous_data")
        if data is None:
            raise PydanticCustomError("previous_data", "未获取到数据列表")

        if (
            module_name
            and project_link
            and any(
                x["module_name"] == module_name and x["project_link"] == project_link
                for x in data
            )
        ):
            raise PydanticCustomError(
                "duplication",
                "PyPI 项目名 {project_link} 加包名 {module_name} 的值与商店重复",
                {"project_link": project_link, "module_name": module_name},
            )

        # 如果一切正常才记录上传时间和版本号
        if project_link is not None:
            # ~none 和 ~fastapi 驱动器的项目名一个是空字符串，一个是 nonebot2[fastapi]
            # 上传时间和版本号均以 nonebot2 为准
            if issubclass(cls, DriverPublishInfo) and (
                project_link == "" or project_link.startswith("nonebot2[")
            ):
                project_link = "nonebot2"

            values["time"] = get_pypi_upload_time(project_link)
            # 只有不是插件测试并且未提供版本号的情况下才获取版本号
            # 插件测试的时候应该总是使用从插件测试获取的版本号，也就是传入的版本号
            if not issubclass(cls, PluginPublishInfo) and "version" not in values:
                values["version"] = get_pypi_version(project_link)

        return values


class PublishInfo(abc.ABC, BaseModel):
    """发布信息"""

    name: str = Field(max_length=NAME_MAX_LENGTH)
    desc: str
    author: str
    author_id: int
    homepage: Annotated[
        str,
        StringConstraints(strip_whitespace=True, pattern=r"^(https?://.*|/docs/.*)$"),
    ]
    tags: list[Tag] = Field(max_length=3)
    is_official: bool = Field(default=False)

    @field_validator("*", mode="wrap")
    @classmethod
    def collect_valid_values(
        cls, v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
    ):
        """收集验证通过的数据

        NOTE: 其他所有的验证器都应该在这个验证器之前执行
        所以不能用 after 模式，只能用 before 模式
        """
        context = info.context
        if context is None:  # pragma: no cover
            raise PydanticCustomError("validation_context", "未获取到验证上下文")

        result = handler(v)
        # 保存成 jsonable 的数据
        # 方便后续使用
        context["valid_data"][info.field_name] = to_jsonable_python(result)
        return result

    @field_validator("homepage", mode="before")
    @classmethod
    def homepage_validator(cls, v: str) -> str:
        if v:
            # 内置驱动器的主页可以不是网址
            if issubclass(cls, DriverPublishInfo) and v.startswith("/docs/"):
                return v
            status_code, msg = check_url(v)
            if status_code != 200:
                raise PydanticCustomError(
                    "homepage",
                    "项目主页无法访问",
                    {"status_code": status_code, "msg": msg},
                )
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def tags_validator(cls, v: str | list[Any]) -> list[dict[str, str]]:
        if not isinstance(v, str):
            # 将值转成 Python dict，避免 model_type 报错
            return to_jsonable_python(v)

        try:
            return load_json(v)
        except Json5DecoderException:
            raise PydanticCustomError("json_type", "JSON 格式不合法")


class PluginPublishInfo(PublishInfo, PyPIMixin):
    """发布插件所需信息"""

    type: str
    """插件类型"""
    supported_adapters: list[str] | None
    """插件支持的适配器"""
    load: bool
    """插件测试结果"""
    metadata: bool
    """插件测试元数据"""
    skip_test: bool
    """是否跳过插件测试"""
    test_config: str = ""
    """插件测试配置"""
    test_output: str = ""
    """插件测试输出"""

    @field_validator("type", mode="before")
    @classmethod
    def type_validator(cls, v: str) -> str:
        if v not in PLUGIN_VALID_TYPE:
            raise PydanticCustomError("plugin.type", "插件类型不符合规范")
        return v

    @field_validator("supported_adapters", mode="before")
    @classmethod
    def supported_adapters_validator(
        cls, v: str | list[str] | None, info: ValidationInfo
    ) -> list[str] | None:
        context = info.context
        if context is None:  # pragma: no cover
            raise PydanticCustomError("validation_context", "未获取到验证上下文")

        skip_test = context.get("skip_test")
        # 如果是从 issue 中获取的数据，需要先解码
        if skip_test and isinstance(v, str):
            try:
                v = load_json(v)
            except Json5DecoderException:
                raise PydanticCustomError("json_type", "JSON 格式不合法")

        # 如果是支持所有适配器，值应该是 None，不需要检查
        if v is None:
            return None

        if not isinstance(v, list | set):
            raise PydanticCustomError("set_type", "值应该是一个集合")

        if any(not isinstance(x, str) for x in v):
            raise PydanticCustomError("set_type", "集合中的值应该是字符串")

        supported_adapters = {resolve_adapter_name(x) for x in v}
        store_adapters = get_adapters()

        missing_adapters = supported_adapters - store_adapters
        if missing_adapters:
            raise PydanticCustomError(
                "supported_adapters.missing",
                "适配器 {missing_adapters_str} 不存在",
                {
                    "missing_adapters": list(missing_adapters),
                    "missing_adapters_str": ", ".join(missing_adapters),
                },
            )
        return sorted(supported_adapters)

    @field_validator("load", mode="before")
    @classmethod
    def plugin_test_load_validator(cls, v: bool, info: ValidationInfo) -> bool:
        context = info.context
        if context is None:
            raise PydanticCustomError("validation_context", "未获取到验证上下文")

        if v or context.get("skip_test"):
            return True
        raise PydanticCustomError(
            "plugin.test",
            "插件无法正常加载",
            {"output": context.get("test_output")},
        )

    @field_validator("metadata", mode="before")
    @classmethod
    def plugin_test_metadata_validator(
        cls, v: bool | None, info: ValidationInfo
    ) -> bool:
        context = info.context
        if context is None:
            raise PydanticCustomError("validation_context", "未获取到验证上下文")

        if not v:
            raise PydanticCustomError(
                "plugin.metadata",
                "插件无法获取到元数据",
                {"load": context.get("load")},
            )
        return v


class AdapterPublishInfo(PublishInfo, PyPIMixin):
    """发布适配器所需信息"""


class BotPublishInfo(PublishInfo):
    """发布机器人所需信息"""

    @model_validator(mode="before")
    @classmethod
    def prevent_duplication(
        cls, values: dict[str, Any], info: ValidationInfo
    ) -> dict[str, Any]:
        name = values.get("name")
        homepage = values.get("homepage")

        context = info.context
        if context is None:  # pragma: no cover
            raise PydanticCustomError("validation_context", "未获取到验证上下文")
        data = context.get("previous_data")
        if data is None:
            raise PydanticCustomError("previous_data", "未获取到数据列表")

        if (
            name
            and homepage
            and any(x["name"] == name and x["homepage"] == homepage for x in data)
        ):
            raise PydanticCustomError(
                "duplication",
                "名称 {name} 加主页 {homepage} 的值与商店重复",
                {"name": name, "homepage": homepage},
            )
        return values


class DriverPublishInfo(PublishInfo, PyPIMixin):
    """发布驱动所需信息"""


PublishInfoModels: TypeAlias = (
    AdapterPublishInfo | BotPublishInfo | DriverPublishInfo | PluginPublishInfo
)


class ValidationDict(BaseModel):
    type: PublishType
    raw_data: dict[str, Any] = {}
    """原始数据"""
    valid_data: dict[str, Any] = {}
    """验证上下文"""
    # 不需要重复验证，应直接传递对应的模型
    info: SkipValidation[PublishInfoModels | None] = None
    """验证通过的信息"""
    errors: list[ErrorDetails] = []

    @property
    def valid(self) -> bool:
        return self.info is not None

    @property
    def name(self) -> str:
        return (
            self.valid_data.get("name")
            or self.raw_data.get("name")
            or self.raw_data.get("project_link")
            or ""
        )

    @property
    def skip_test(self) -> bool:
        return self.raw_data.get("skip_test", False)
