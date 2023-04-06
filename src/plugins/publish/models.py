from enum import Enum

from pydantic import BaseModel


class PublishType(Enum):
    """发布的类型

    值为标签名
    """

    BOT = "Bot"
    PLUGIN = "Plugin"
    ADAPTER = "Adapter"


class RepoInfo(BaseModel):
    """仓库信息"""

    owner: str
    name: str
