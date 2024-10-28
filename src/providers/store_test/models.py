from datetime import datetime
from typing import Any, Literal, Self
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)
from pydantic_extra_types.color import Color

from src.providers.validation.models import (
    AdapterPublishInfo,
    BotPublishInfo,
    DriverPublishInfo,
    PluginPublishInfo,
    Tag,
)


class TagModel(BaseModel):
    tags: list[Tag]

    @field_validator("tags", mode="before")
    @classmethod
    def tags_validator(cls, v: list[dict[str, Any]]):
        return [
            Tag.model_construct(label=tag["label"], color=Color(tag["color"]))
            for tag in v
        ]


# region 仓库数据模型
class StoreAdapter(TagModel):
    """NoneBot 仓库中的适配器数据"""

    module_name: str
    project_link: str
    name: str
    desc: str
    author_id: int
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
            tags=publish_info.tags,
            is_official=publish_info.is_official,
        )


class StoreBot(TagModel):
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


class StoreDriver(TagModel):
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


class StorePlugin(TagModel):
    """NoneBot 仓库中的插件数据"""

    module_name: str
    project_link: str
    author_id: int
    tags: list[Tag]
    is_official: bool

    @classmethod
    def from_publish_inf(cls, publish_info: PluginPublishInfo) -> Self:
        return cls(
            module_name=publish_info.module_name,
            project_link=publish_info.project_link,
            author_id=publish_info.author_id,
            tags=publish_info.tags,
            is_official=publish_info.is_official,
        )


# endregion


# region 商店数据模型
class Adapter(TagModel):
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


class Bot(TagModel):
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


class Driver(TagModel):
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


class Plugin(TagModel):
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


class TestResult(BaseModel):
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
