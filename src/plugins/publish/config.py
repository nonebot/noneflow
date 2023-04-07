from pathlib import Path

from nonebot import get_driver
from pydantic import BaseModel, Extra


class PublishConfig(BaseModel):
    base: str
    plugin_path: Path
    bot_path: Path
    adapter_path: Path


class Config(BaseModel, extra=Extra.ignore):
    input_config: PublishConfig
    github_repository: str
    github_run_id: str
    skip_plugin_test: bool = False
    plugin_test_result: bool = False
    plugin_test_output: str = ""


plugin_config = Config.parse_obj(get_driver().config)
