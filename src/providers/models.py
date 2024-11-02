# ruff: noqa: UP040
from datetime import datetime
from typing import Any, Literal, Self, TypeAlias
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from src.providers.docker_test import Metadata
from src.providers.store_test.constants import BOT_KEY_TEMPLATE, PYPI_KEY_TEMPLATE
from src.providers.validation.models import (
    AdapterPublishInfo,
    BotPublishInfo,
    DriverPublishInfo,
    PluginPublishInfo,
    PublishInfoModels,
    PublishType,
    Tag,
)


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
            tags=publish_info.tags,
            is_official=publish_info.is_official,
        )


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
            tags=publish_info.tags,
            is_official=publish_info.is_official,
        )


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
            tags=publish_info.tags,
            is_official=publish_info.is_official,
        )


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
            tags=publish_info.tags,
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
            tags=publish_info.tags,
            is_official=publish_info.is_official,
        )


class RegistryBot(BaseModel):
    """NoneBot 商店机器人数据"""

    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: bool

    @classmethod
    def from_publish_info(cls, publish_info: BotPublishInfo) -> Self:
        return cls(
            name=publish_info.name,
            desc=publish_info.desc,
            author=publish_info.author,
            homepage=publish_info.homepage,
            tags=publish_info.tags,
            is_official=publish_info.is_official,
        )


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

    @classmethod
    def from_publish_info(cls, publish_info: DriverPublishInfo) -> Self:
        return cls(
            module_name=publish_info.module_name,
            project_link=publish_info.project_link,
            name=publish_info.name,
            desc=publish_info.desc,
            author=publish_info.author,
            homepage=publish_info.homepage,
            tags=publish_info.tags,
            is_official=publish_info.is_official,
        )


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

    @classmethod
    def from_publish_info(cls, publish_info: PluginPublishInfo) -> Self:
        if publish_info.time is None:
            raise ValueError("上传时间不能为空")

        return cls(
            module_name=publish_info.module_name,
            project_link=publish_info.project_link,
            name=publish_info.name,
            desc=publish_info.desc,
            author=publish_info.author,
            homepage=publish_info.homepage,
            tags=publish_info.tags,
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


RegistryModels: TypeAlias = (
    RegistryAdapter | RegistryBot | RegistryDriver | RegistryPlugin
)
# endregion


class StoreTestResult(BaseModel):
    time: str = Field(
        default_factory=lambda: datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    )
    config: str = ""
    version: str | None
    test_env: dict[str, bool] | None = None
    """
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
                ).model_dump(),
            },
        )


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
