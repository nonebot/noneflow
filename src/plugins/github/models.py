import io
import os
import zipfile
from pathlib import Path
from typing import Self

from githubkit import AppAuthStrategy, GitHub
from githubkit.rest import Issue
from pydantic import BaseModel

from src.providers.constants import REGISTRY_DATA_NAME
from src.providers.models import (
    PluginPublishInfo,
    PublishInfoModels,
    RegistryModels,
    StoreTestResult,
    to_registry,
)


class RepoInfo(BaseModel):
    """仓库信息"""

    owner: str
    repo: str

    @classmethod
    def from_issue(cls, issue: Issue) -> "RepoInfo":
        assert issue.repository
        return RepoInfo(
            owner=issue.repository.owner.login,
            repo=issue.repository.name,
        )

    def __str__(self) -> str:
        return f"{self.owner}/{self.repo}"


class AuthorInfo(BaseModel):
    """作者信息"""

    author: str = ""
    author_id: int = 0

    @classmethod
    def from_issue(cls, issue: Issue) -> "AuthorInfo":
        return AuthorInfo(
            author=issue.user.login if issue.user else "",
            author_id=issue.user.id if issue.user else 0,
        )


class RegistryArtifactData(BaseModel):
    """注册表数据

    通过 GitHub Action Artifact 传递数据
    """

    registry: RegistryModels
    result: StoreTestResult | None

    @classmethod
    def from_info(cls, info: PublishInfoModels) -> Self:
        return cls(
            registry=to_registry(info),
            result=StoreTestResult.from_info(info)
            if isinstance(info, PluginPublishInfo)
            else None,
        )

    def save(self, path: Path) -> None:
        """将注册表数据保存到指定路径"""
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        if not path.is_dir():
            raise ValueError(f"路径 {path} 不是一个目录")

        file_path = path / REGISTRY_DATA_NAME
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2, exclude_none=True))


class RegistryUpdatePayload(BaseModel):
    """注册表更新数据

    通过 GitHub Action Artifact 传递数据
    """

    repo_info: RepoInfo
    artifact_id: int

    def get_artifact_data(self) -> RegistryArtifactData:
        """获取注册表数据"""

        app_id = os.getenv("APP_ID")
        private_key = os.getenv("PRIVATE_KEY")

        if app_id is None or private_key is None:
            raise ValueError("APP_ID 或 PRIVATE_KEY 未设置")

        github = GitHub(AppAuthStrategy(app_id=app_id, private_key=private_key))

        resp = github.rest.apps.get_repo_installation(
            self.repo_info.owner, self.repo_info.repo
        )
        repo_installation = resp.parsed_data

        installation_github = github.with_auth(
            github.auth.as_installation(repo_installation.id)
        )

        resp = installation_github.rest.actions.download_artifact(
            owner=self.repo_info.owner,
            repo=self.repo_info.repo,
            artifact_id=self.artifact_id,
            archive_format="zip",
        )

        zip_buffer = io.BytesIO(resp.content)
        with zipfile.ZipFile(zip_buffer) as zip_file:
            with zip_file.open(REGISTRY_DATA_NAME) as json_file:
                json_data = json_file.read()
                return RegistryArtifactData.model_validate_json(json_data)
