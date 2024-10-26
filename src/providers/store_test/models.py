from datetime import datetime
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)
from pydantic_extra_types.color import Color

from src.providers.validation.models import Metadata, Tag


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


class StoreBot(TagModel):
    """NoneBot 仓库中的机器人数据"""

    name: str
    desc: str
    author_id: int
    homepage: str
    tags: list[Tag]
    is_official: bool


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


class StorePlugin(TagModel):
    """NoneBot 仓库中的插件数据"""

    module_name: str
    project_link: str
    author_id: int
    tags: list[Tag]
    is_official: bool


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


class Bot(TagModel):
    """NoneBot 商店机器人数据"""

    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: bool


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

    def metadata(self) -> Metadata:
        return Metadata.model_construct(
            name=self.name,
            description=self.desc,
            homepage=self.homepage,
            type=self.type,
            supported_adapters=self.supported_adapters,
        )


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


class DockerTestResult(BaseModel):
    """Docker 测试结果"""

    run: bool  # 是否运行
    load: bool  # 是否加载成功
    version: str | None = None
    config: str = ""
    # 测试环境 python==3.10 pytest==6.2.5 nonebot2==2.0.0a1 ...
    test_env: str = Field(default="unknown")
    metadata: Metadata | None
    outputs: list[str]

    @field_validator("metadata", mode="before")
    @classmethod
    def metadata_validator(cls, v: Any):
        if v:
            return v
        return None

    @field_validator("config", mode="before")
    @classmethod
    def config_validator(cls, v: str | None):
        return v or ""
