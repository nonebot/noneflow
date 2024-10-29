from pathlib import Path

from pydantic import BaseModel, ConfigDict


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
