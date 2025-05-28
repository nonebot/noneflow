from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import RepoInfo


class PublishConfig(BaseModel):
    base: str
    plugin_path: Path
    bot_path: Path
    adapter_path: Path
    registry_repository: RepoInfo = Field(
        default=RepoInfo(owner="nonebot", repo="registry")
    )
    store_repository: RepoInfo = Field(
        default=RepoInfo(owner="nonebot", repo="nonebot2")
    )
    artifact_path: Path = Field(
        default=Path("artifact"),
        description="Artifact 存储路径，默认是 `artifact` 目录",
    )

    @field_validator("registry_repository", "store_repository", mode="before")
    @classmethod
    def check_repositorys(cls, v: str) -> RepoInfo | None:
        if not v:
            return None
        owner, repo = v.split("/")
        return RepoInfo(owner=owner, repo=repo)


class Config(BaseModel, extra="ignore"):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    input_config: PublishConfig
    github_repository: str
    github_run_id: str
    github_step_summary: Path
