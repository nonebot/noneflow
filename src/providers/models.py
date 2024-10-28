from typing import Any, Self

from pydantic import BaseModel

from src.providers.validation.models import (
    AdapterPublishInfo,
    BotPublishInfo,
    DriverPublishInfo,
    PluginPublishInfo,
    PublishInfo,
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

    @classmethod
    def from_publish_info(cls, publish_info: PluginPublishInfo) -> Self:
        return cls(
            module_name=publish_info.module_name,
            project_link=publish_info.project_link,
            author_id=publish_info.author_id,
            tags=publish_info.tags,
            is_official=publish_info.is_official,
        )


def to_store(info: PublishInfo) -> dict[str, Any]:
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
        case _:
            raise ValueError("未知的发布信息类型")

    return store.model_dump()


# endregion


# region 商店数据模型
class Adapter(BaseModel):
    """NoneBot 商店适配器数据"""

    module_name: str
    project_link: str
    name: str
    desc: str
    author: str
    tags: list[Tag]
    is_official: bool

    @classmethod
    def from_publish_info(cls, publish_info: AdapterPublishInfo) -> Self:
        return cls(
            module_name=publish_info.module_name,
            project_link=publish_info.project_link,
            name=publish_info.name,
            desc=publish_info.desc,
            author=publish_info.author,
            tags=publish_info.tags,
            is_official=publish_info.is_official,
        )


class Bot(BaseModel):
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


class Driver(BaseModel):
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


class Plugin(BaseModel):
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


# endregion
