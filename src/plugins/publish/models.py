from pydantic import BaseModel


class RepoInfo(BaseModel):
    """仓库信息"""

    owner: str
    repo: str
