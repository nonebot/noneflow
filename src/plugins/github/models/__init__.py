from pydantic import BaseModel


class RepoInfo(BaseModel):
    """仓库信息"""

    owner: str
    repo: str


from .git import GitHandler as GitHandler
from .github import GithubHandler as GithubHandler
from .issue import IssueHandler as IssueHandler

__all__ = ["GitHandler", "GithubHandler", "IssueHandler", "RepoInfo"]
