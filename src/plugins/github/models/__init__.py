from githubkit.rest import Issue
from pydantic import BaseModel


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


from .git import GitHandler as GitHandler
from .github import GithubHandler as GithubHandler
from .issue import IssueHandler as IssueHandler

__all__ = ["GitHandler", "GithubHandler", "IssueHandler", "RepoInfo", "AuthorInfo"]
