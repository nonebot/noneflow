import abc
import json
from enum import Enum
from pathlib import Path
from typing import Optional

from github.Issue import Issue
from pydantic import BaseModel, BaseSettings, SecretStr


class PartialGithubEventHeadCommit(BaseModel):
    message: str


class PartialGitHubEventIssue(BaseModel):
    number: int


class PartialGitHubIssuesEvent(BaseModel):
    """议题事件

    https://docs.github.com/cn/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#issues
    """

    action: str
    issue: PartialGitHubEventIssue


class PartialGitHubPullRequestEvent(BaseModel):
    """拉取请求事件

    https://docs.github.com/cn/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#pull_request
    """

    action: str
    pull_request: PartialGitHubEventIssue


class PartialGitHubPushEvent(BaseModel):
    """推送事件

    https://docs.github.com/cn/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#push
    """

    head_commit: PartialGithubEventHeadCommit


class Config(BaseModel):
    base: str
    plugin_path: Path
    bot_path: Path
    adapter_path: Path


class Settings(BaseSettings):
    input_token: SecretStr
    input_config: Config
    github_repository: str
    github_event_name: Optional[str] = None
    github_event_path: Path


class PublishType(Enum):
    """发布的类型

    值为标签名
    """

    BOT = "Bot"
    PLUGIN = "Plugin"
    ADAPTER = "Adapter"


class PublishInfo(abc.ABC, BaseModel):
    """发布信息"""

    name: str
    desc: str
    author: str
    homepage: str
    tags: list[str]
    is_official: bool

    def _update_file(self, path: Path):
        """更新文件"""
        with path.open("rw", encoding="utf-8") as f:
            data: list[dict[str, str]] = json.load(f)
            data.append(self.dict())
            json.dump(data, f, ensure_ascii=False, indent=2)

    @abc.abstractmethod
    def update_file(self, settings: Settings) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get_type(self) -> PublishType:
        """获取发布类型"""
        raise NotImplementedError


class BotInfo(PublishInfo):
    """发布机器人所需信息"""

    def get_type(self) -> PublishType:
        return PublishType.BOT

    def update_file(self, settings: Settings) -> None:
        self._update_file(settings.input_config.bot_path)

    @classmethod
    def from_issue(cls, issue: Issue) -> "BotInfo":
        return BotInfo()


class PluginInfo(PublishInfo):
    """发布插件所需信息"""

    module_name: str
    project_link: str

    def get_type(self) -> PublishType:
        return PublishType.PLUGIN

    def update_file(self, settings: Settings) -> None:
        self._update_file(settings.input_config.plugin_path)

    @classmethod
    def from_issue(cls, issue: Issue) -> "PluginInfo":
        return PluginInfo()


class AdapterInfo(PublishInfo):
    """发布适配器所需信息"""

    module_name: str
    project_link: str

    def get_type(self) -> PublishType:
        return PublishType.ADAPTER

    def update_file(self, settings: Settings) -> None:
        self._update_file(settings.input_config.adapter_path)

    @classmethod
    def from_issue(cls, issue: Issue) -> "AdapterInfo":
        return AdapterInfo()
