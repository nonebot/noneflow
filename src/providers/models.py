# ruff: noqa: UP040
from datetime import datetime
from typing import Any, Literal, Self, TypeAlias

from pydantic import BaseModel, Field, field_serializer, field_validator
from pydantic_extra_types.color import Color

from src.providers.constants import BOT_KEY_TEMPLATE, PYPI_KEY_TEMPLATE, TIME_ZONE
from src.providers.docker_test import Metadata
from src.providers.utils import get_author_name, get_pypi_upload_time, get_pypi_version
from src.providers.validation import validate_info
from src.providers.validation.models import (
    AdapterPublishInfo,
    BotPublishInfo,
    DriverPublishInfo,
    PluginPublishInfo,
    PublishInfoModels,
    PublishType,
)


class Tag(BaseModel):
    """标签"""

    label: str
    color: Color

    @field_serializer("color")
    def color_serializer(self, color: Color):
        return color.as_hex(format="long")


# region 仓库数据模型
class StoreAdapter(BaseModel):
    """NoneBot 仓库中的适配器数据"""

    module_name: str
    project_link: str
    name: str
    desc: str
    author_id: int
    homepage: str
    tags: list[Tag]
    is_official: bool

    @property
    def key(self):
        return PYPI_KEY_TEMPLATE.format(
            project_link=self.project_link, module_name=self.module_name
        )

    @classmethod
    def from_publish_info(cls, publish_info: AdapterPublishInfo) -> Self:
        return cls(
            module_name=publish_info.module_name,
            project_link=publish_info.project_link,
            name=publish_info.name,
            desc=publish_info.desc,
            author_id=publish_info.author_id,
            homepage=publish_info.homepage,
            tags=[Tag(label=tag.label, color=tag.color) for tag in publish_info.tags],
            is_official=publish_info.is_official,
        )

    def to_registry(self) -> "RegistryAdapter":
        """将仓库数据转换为注册表数据

        将获取 author 信息，重新验证数据
        """
        author = get_author_name(self.author_id)
        result = validate_info(
            PublishType.ADAPTER,
            {**self.model_dump(), "author": author},
            [],
        )
        if result.info is None or not isinstance(result.info, AdapterPublishInfo):
            raise ValueError(f"数据验证失败: {result.errors}")
        return RegistryAdapter.from_publish_info(result.info)


class StoreBot(BaseModel):
    """NoneBot 仓库中的机器人数据"""

    name: str
    desc: str
    author_id: int
    homepage: str
    tags: list[Tag]
    is_official: bool

    @property
    def key(self):
        return BOT_KEY_TEMPLATE.format(name=self.name, homepage=self.homepage)

    @classmethod
    def from_publish_info(cls, publish_info: BotPublishInfo) -> Self:
        return cls(
            name=publish_info.name,
            desc=publish_info.desc,
            author_id=publish_info.author_id,
            homepage=publish_info.homepage,
            tags=[Tag(label=tag.label, color=tag.color) for tag in publish_info.tags],
            is_official=publish_info.is_official,
        )

    def to_registry(self) -> "RegistryBot":
        """将仓库数据转换为注册表数据

        将获取 author 信息，重新验证数据
        """
        author = get_author_name(self.author_id)
        result = validate_info(
            PublishType.BOT,
            {**self.model_dump(), "author": author},
            [],
        )
        if result.info is None or not isinstance(result.info, BotPublishInfo):
            raise ValueError(f"数据验证失败: {result.errors}")
        return RegistryBot.from_publish_info(result.info)


class StoreDriver(BaseModel):
    """NoneBot 仓库中的驱动数据"""

    module_name: str
    project_link: str
    name: str
    desc: str
    author_id: int
    homepage: str
    tags: list[Tag]
    is_official: bool

    @property
    def key(self):
        return PYPI_KEY_TEMPLATE.format(
            project_link=self.project_link, module_name=self.module_name
        )

    @classmethod
    def from_publish_info(cls, publish_info: DriverPublishInfo) -> Self:
        return cls(
            module_name=publish_info.module_name,
            project_link=publish_info.project_link,
            name=publish_info.name,
            desc=publish_info.desc,
            author_id=publish_info.author_id,
            homepage=publish_info.homepage,
            tags=[Tag(label=tag.label, color=tag.color) for tag in publish_info.tags],
            is_official=publish_info.is_official,
        )

    def to_registry(self) -> "RegistryDriver":
        """将仓库数据转换为注册表数据

        将获取 author 信息，重新验证数据
        """
        author = get_author_name(self.author_id)
        result = validate_info(
            PublishType.DRIVER,
            {**self.model_dump(), "author": author},
            [],
        )
        if result.info is None or not isinstance(result.info, DriverPublishInfo):
            raise ValueError(f"数据验证失败: {result.errors}")
        return RegistryDriver.from_publish_info(result.info)


class StorePlugin(BaseModel):
    """NoneBot 仓库中的插件数据"""

    module_name: str
    project_link: str
    author_id: int
    tags: list[Tag]
    is_official: bool

    @property
    def key(self):
        return PYPI_KEY_TEMPLATE.format(
            project_link=self.project_link, module_name=self.module_name
        )

    @classmethod
    def from_publish_info(cls, publish_info: PluginPublishInfo) -> Self:
        return cls(
            module_name=publish_info.module_name,
            project_link=publish_info.project_link,
            author_id=publish_info.author_id,
            tags=[Tag(label=tag.label, color=tag.color) for tag in publish_info.tags],
            is_official=publish_info.is_official,
        )


def to_store(info: PublishInfoModels) -> dict[str, Any]:
    store = None
    match info:
        case AdapterPublishInfo():
            store = StoreAdapter.from_publish_info(info)
        case BotPublishInfo():
            store = StoreBot.from_publish_info(info)
        case DriverPublishInfo():
            store = StoreDriver.from_publish_info(info)
        case PluginPublishInfo():
            store = StorePlugin.from_publish_info(info)

    return store.model_dump()


StoreModels: TypeAlias = StoreAdapter | StoreBot | StoreDriver | StorePlugin
# endregion


# region 商店数据模型
class RegistryAdapter(BaseModel):
    """NoneBot 商店适配器数据"""

    module_name: str
    project_link: str
    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: bool
    time: str
    version: str

    @property
    def key(self):
        return PYPI_KEY_TEMPLATE.format(
            project_link=self.project_link, module_name=self.module_name
        )

    @classmethod
    def from_publish_info(cls, publish_info: AdapterPublishInfo) -> Self:
        return cls(
            module_name=publish_info.module_name,
            project_link=publish_info.project_link,
            name=publish_info.name,
            desc=publish_info.desc,
            author=publish_info.author,
            homepage=publish_info.homepage,
            tags=[Tag(label=tag.label, color=tag.color) for tag in publish_info.tags],
            is_official=publish_info.is_official,
            time=publish_info.time,
            version=publish_info.version,
        )

    def update(self, store: StoreAdapter) -> "RegistryAdapter":
        """根据商店数据更新注册表数据"""
        version = get_pypi_version(self.project_link)
        time = get_pypi_upload_time(self.project_link)

        data = self.model_dump()
        data.update(store.model_dump())
        data.update(version=version, time=time)

        return RegistryAdapter(**data)


class RegistryBot(BaseModel):
    """NoneBot 商店机器人数据"""

    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: bool

    @property
    def key(self):
        return BOT_KEY_TEMPLATE.format(name=self.name, homepage=self.homepage)

    @classmethod
    def from_publish_info(cls, publish_info: BotPublishInfo) -> Self:
        return cls(
            name=publish_info.name,
            desc=publish_info.desc,
            author=publish_info.author,
            homepage=publish_info.homepage,
            tags=[Tag(label=tag.label, color=tag.color) for tag in publish_info.tags],
            is_official=publish_info.is_official,
        )

    def update(self, store: StoreBot) -> "RegistryBot":
        """根据商店数据更新注册表数据"""
        data = self.model_dump()
        data.update(store.model_dump())
        return RegistryBot(**data)


class RegistryDriver(BaseModel):
    """NoneBot 商店驱动数据"""

    module_name: str
    project_link: str
    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: bool
    time: str
    version: str

    @property
    def key(self):
        return PYPI_KEY_TEMPLATE.format(
            project_link=self.project_link, module_name=self.module_name
        )

    @classmethod
    def from_publish_info(cls, publish_info: DriverPublishInfo) -> Self:
        return cls(
            module_name=publish_info.module_name,
            project_link=publish_info.project_link,
            name=publish_info.name,
            desc=publish_info.desc,
            author=publish_info.author,
            homepage=publish_info.homepage,
            tags=[Tag(label=tag.label, color=tag.color) for tag in publish_info.tags],
            is_official=publish_info.is_official,
            time=publish_info.time,
            version=publish_info.version,
        )

    def update(self, store: StoreDriver) -> "RegistryDriver":
        """根据商店数据更新注册表数据"""
        # ~none 和 ~fastapi 驱动器的项目名一个是空字符串，一个是 nonebot2[fastapi]
        # 上传时间和版本号均以 nonebot2 为准
        project_link = self.project_link
        if project_link == "" or project_link.startswith("nonebot2["):
            project_link = "nonebot2"
        version = get_pypi_version(project_link)
        time = get_pypi_upload_time(project_link)

        data = self.model_dump()
        data.update(store.model_dump())
        data.update(version=version, time=time)

        return RegistryDriver(**data)


class RegistryPlugin(BaseModel):
    """NoneBot 商店插件数据"""

    module_name: str
    project_link: str
    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: bool
    type: str | None
    supported_adapters: list[str] | None = None
    valid: bool
    time: str
    version: str
    skip_test: bool

    @property
    def key(self):
        return PYPI_KEY_TEMPLATE.format(
            project_link=self.project_link, module_name=self.module_name
        )

    @classmethod
    def from_publish_info(cls, publish_info: PluginPublishInfo) -> Self:
        return cls(
            module_name=publish_info.module_name,
            project_link=publish_info.project_link,
            name=publish_info.name,
            desc=publish_info.desc,
            author=publish_info.author,
            homepage=publish_info.homepage,
            tags=[Tag(label=tag.label, color=tag.color) for tag in publish_info.tags],
            is_official=publish_info.is_official,
            type=publish_info.type,
            supported_adapters=publish_info.supported_adapters,
            valid=True,
            time=publish_info.time,
            version=publish_info.version,
            skip_test=publish_info.skip_test,
        )

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "desc": self.desc,
            "homepage": self.homepage,
            "type": self.type,
            "supported_adapters": self.supported_adapters,
        }

    def update(self, store: StorePlugin) -> "RegistryPlugin":
        """根据商店数据更新注册表数据"""
        # TODO: 如果 author_id 变化，应该重新获取 author
        data = self.model_dump()
        data.update(store.model_dump())
        return RegistryPlugin(**data)


RegistryModels: TypeAlias = (
    RegistryAdapter | RegistryBot | RegistryDriver | RegistryPlugin
)
# endregion


class StoreTestResult(BaseModel):
    time: str = Field(default_factory=lambda: datetime.now(TIME_ZONE).isoformat())
    """测试时间"""
    config: str = ""
    """测试插件的配置"""
    version: str | None
    """测试插件的版本号"""
    test_env: dict[str, bool] | None = None
    """测试环境

    键为测试环境 python==3.10 pytest==6.2.5 nonebot2==2.0.0a1 ...
    值为在该环境下是否通过插件测试
    """
    results: dict[Literal["validation", "load", "metadata"], bool]
    outputs: dict[Literal["validation", "load", "metadata"], Any]

    @classmethod
    def from_info(cls, info: PluginPublishInfo) -> Self:
        return cls(
            config=info.test_config,
            version=info.version,
            test_env={"python==3.12": True},
            results={"validation": True, "load": True, "metadata": True},
            outputs={
                "validation": None,
                "load": info.test_output,
                "metadata": Metadata(
                    name=info.name,
                    desc=info.desc,
                    homepage=info.homepage,
                    type=info.type,
                    supported_adapters=info.supported_adapters,
                ),
            },
        )

    @field_validator("outputs", mode="before")
    @classmethod
    def outputs_metadata_validator(cls, v: dict[str, Any]) -> dict[str, Any]:
        # nonebot2 中插件元数据的字段和商店中的字段不一致
        if v["metadata"] is not None:
            metadata = {}
            # 将 metadata 中 desc 字段重命名为 description
            # 同时保证其他字段顺序不变
            for key, value in v["metadata"].items():
                if key == "desc":
                    metadata["description"] = value
                else:
                    metadata[key] = value
            v["metadata"] = metadata
        return v


class RegistryUpdatePayload(BaseModel):
    type: PublishType
    registry: RegistryModels
    result: StoreTestResult | None = None

    @classmethod
    def from_info(cls, info: PublishInfoModels) -> Self:
        match info:
            case AdapterPublishInfo():
                type = PublishType.ADAPTER
                registry = RegistryAdapter.from_publish_info(info)
                result = None
            case BotPublishInfo():
                type = PublishType.BOT
                registry = RegistryBot.from_publish_info(info)
                result = None
            case DriverPublishInfo():
                type = PublishType.DRIVER
                registry = RegistryDriver.from_publish_info(info)
                result = None
            case PluginPublishInfo():
                type = PublishType.PLUGIN
                registry = RegistryPlugin.from_publish_info(info)
                result = StoreTestResult.from_info(info)

        return cls(type=type, registry=registry, result=result)
