import abc
import json
from enum import Enum
from typing import TYPE_CHECKING, Any, TypedDict

from pydantic import BaseModel, Field, root_validator, validator
from pydantic.color import Color
from pydantic.errors import JsonError, ListError

if TYPE_CHECKING:
    from pydantic.error_wrappers import ErrorDict as PydanticErrorDict

    class ErrorDict(PydanticErrorDict, total=False):
        input: Any


from .constants import (
    MAX_NAME_LENGTH,
    PLUGIN_VALID_TYPE,
    PYPI_PACKAGE_NAME_PATTERN,
    PYTHON_MODULE_NAME_REGEX,
)
from .errors import (
    DuplicationError,
    HomepageError,
    ModuleNameError,
    PluginSupportedAdaptersMissingError,
    PluginTypeError,
    ProjectLinkNameError,
    ProjectLinkNotFoundError,
)
from .utils import check_pypi, check_url, get_adapters, resolve_adapter_name


class ValidationDict(TypedDict):
    valid: bool
    type: "PublishType"
    name: str
    author: str
    data: dict[str, Any]
    errors: "list[ErrorDict]"


class PublishType(Enum):
    """发布的类型

    值为标签名
    """

    BOT = "Bot"
    PLUGIN = "Plugin"
    ADAPTER = "Adapter"


class PyPIMixin(BaseModel):
    module_name: str
    project_link: str

    previous_data: list[dict[str, Any]]

    @validator("module_name", pre=True)
    def module_name_validator(cls, v: str) -> str:
        if not PYTHON_MODULE_NAME_REGEX.match(v):
            raise ModuleNameError()
        return v

    @validator("project_link", pre=True)
    def project_link_validator(cls, v: str) -> str:
        if not PYPI_PACKAGE_NAME_PATTERN.match(v):
            raise ProjectLinkNameError()

        if v and not check_pypi(v):
            raise ProjectLinkNotFoundError()
        return v

    @root_validator
    def prevent_duplication(cls, values: dict[str, Any]) -> dict[str, Any]:
        module_name = values.get("module_name")
        project_link = values.get("project_link")

        data = values.get("previous_data")
        if data is None:
            raise ValueError("未获取到数据列表")

        if (
            module_name
            and project_link
            and any(
                map(
                    lambda x: x["module_name"] == module_name
                    and x["project_link"] == project_link,
                    data,
                )
            )
        ):
            raise DuplicationError(project_link=project_link, module_name=module_name)
        return values


class Tag(BaseModel):
    """标签"""

    label: str = Field(max_length=10)
    color: Color


class PublishInfo(abc.ABC, BaseModel):
    """发布信息"""

    name: str = Field(max_length=MAX_NAME_LENGTH)
    desc: str
    author: str
    homepage: str
    tags: list[Tag] = Field(max_items=3)
    is_official: bool = False

    @validator("homepage", pre=True)
    def homepage_validator(cls, v: str) -> str:
        if v:
            status_code, msg = check_url(v)
            if status_code != 200:
                raise HomepageError(status_code=status_code, msg=msg)
        return v

    @validator("tags", pre=True)
    def tags_validator(cls, v: str) -> list[dict[str, str]]:
        try:
            tags: list[Any] | Any = json.loads(v)
        except json.JSONDecodeError:
            raise JsonError()
        return tags

    @classmethod
    @abc.abstractmethod
    def get_type(cls) -> PublishType:
        """获取发布类型"""
        raise NotImplementedError


class PluginPublishInfo(PublishInfo, PyPIMixin):
    """发布插件所需信息"""

    type: str
    """插件类型"""
    supported_adapters: list[str] | None
    """插件支持的适配器"""

    @validator("type", pre=True)
    def type_validator(cls, v: str) -> str:
        if v not in PLUGIN_VALID_TYPE:
            raise PluginTypeError()
        return v

    @validator("supported_adapters", pre=True)
    def supported_adapters_validator(
        cls, v: str | list[str] | None
    ) -> list[str] | None:
        # 如果是从 issue 中获取的数据，需要先解码
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                raise JsonError()

        # 如果是支持所有适配器，值应该是 None，不需要检查
        if v is None:
            return None

        if not isinstance(v, list):
            raise ListError()

        supported_adapters = {resolve_adapter_name(x) for x in v}
        store_adapters = get_adapters()

        missing_adapters = supported_adapters - store_adapters
        if missing_adapters:
            raise PluginSupportedAdaptersMissingError(missing_adapters=missing_adapters)
        return sorted(supported_adapters)

    @classmethod
    def get_type(cls) -> PublishType:
        return PublishType.PLUGIN


class AdapterPublishInfo(PublishInfo, PyPIMixin):
    """发布适配器所需信息"""

    @classmethod
    def get_type(cls) -> PublishType:
        return PublishType.ADAPTER


class BotPublishInfo(PublishInfo):
    """发布机器人所需信息"""

    @classmethod
    def get_type(cls) -> PublishType:
        return PublishType.BOT
