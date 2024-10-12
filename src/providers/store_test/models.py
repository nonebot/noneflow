from datetime import datetime
from typing import Any, Literal
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic_extra_types.color import Color


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


class TagModel(BaseModel):
    tags: list[Tag]

    @field_validator("tags", mode="before")
    @classmethod
    def tags_validator(cls, v: list[dict[str, Any]]):
        return [
            Tag.model_construct(label=tag["label"], color=Color(tag["color"]))
            for tag in v
        ]


class StorePlugin(TagModel):
    """NoneBot 仓库中的插件数据"""

    module_name: str
    project_link: str
    author_id: int
    tags: list[Tag]
    is_official: bool


class Metadata(BaseModel):
    """插件元数据"""

    name: str
    desc: str
    homepage: str
    type: str | None = None
    supported_adapters: list[str] | None = None

    @model_validator(mode="before")
    @classmethod
    def model_validator(cls, data: dict[str, Any]):
        if data.get("desc") is None:
            data["desc"] = data.get("description")
        return data


class Plugin(TagModel):
    """NoneBot 商店插件数据"""

    module_name: str
    project_link: str
    name: str
    desc: str
    author: str
    author_id: int
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


class TestResult(BaseModel):
    time: str = Field(
        default_factory=lambda: datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    )
    config: str = ""
    version: str | None
    test_env: dict[str, bool] | None = None
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
