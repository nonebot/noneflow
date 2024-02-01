from pathlib import Path
from typing import Any

from nonebot import get_driver
from pydantic import BaseModel, ConfigDict, field_validator

from src.utils.plugin_test import strip_ansi


class PublishConfig(BaseModel):
    base: str
    plugin_path: Path
    bot_path: Path
    adapter_path: Path
    registry_repository: str = "nonebot/registry"


class Config(BaseModel, extra="ignore"):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    input_config: PublishConfig
    github_repository: str
    github_run_id: str
    skip_plugin_test: bool = False
    plugin_test_result: bool = False
    plugin_test_output: str = ""
    plugin_test_metadata: dict[str, Any] | None = None

    @field_validator("plugin_test_result", mode="before")
    @classmethod
    def plugin_test_result_validator(cls, v):
        # 如果插件测试没有运行时，会得到一个空字符串
        # 这里将其转换为布尔值，不然会报错
        if v == "":
            return False
        return v

    @field_validator("plugin_test_metadata", mode="before")
    @classmethod
    def plugin_test_metadata_validator(cls, v):
        # 如果插件测试没有运行时，会得到一个空字符串
        # 这里将其转换为 None，不然会报错
        if v == "":
            return None
        return v

    @field_validator("plugin_test_output", mode="before")
    @classmethod
    def plugin_test_output_validator(cls, v):
        """移除 ANSI 转义字符"""
        return strip_ansi(v)


plugin_config = Config.model_validate(dict(get_driver().config))
