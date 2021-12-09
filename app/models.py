import abc
import json
from enum import Enum
from pathlib import Path
from typing import Optional

import requests
from github.Issue import Issue
from pydantic import BaseModel, BaseSettings, PrivateAttr, SecretStr

from .models import AdapterPublishInfo, PluginPublishInfo, PublishInfo


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

    _homepage_status_code: Optional[int] = PrivateAttr()

    def _update_file(self, path: Path):
        with path.open("rw", encoding="utf-8") as f:
            data: list[dict[str, str]] = json.load(f)
            data.append(self.dict())
            json.dump(data, f, ensure_ascii=False, indent=2)

    @abc.abstractmethod
    def update_file(self, settings: Settings) -> None:
        """更新文件"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_type(self) -> PublishType:
        """获取发布类型"""
        raise NotImplementedError

    @abc.abstractmethod
    def is_valid(self) -> bool:
        """检查是否满足要求

        返回错误列表，如果为空则说明满足要求
        """
        raise NotImplementedError

    def homepage_status_code(self) -> Optional[int]:
        """主页状态码"""
        if not self._homepage_status_code:
            self._homepage_status_code = check_url(self.homepage)
        return self._homepage_status_code

    def homepage_is_valid(self) -> bool:
        """主页是否可用"""
        return self.homepage_status_code() == 200

    def validate_message(self)-> str:
        return generate_message(self)

class BotPublishInfo(PublishInfo):
    """发布机器人所需信息"""

    def get_type(self) -> PublishType:
        return PublishType.BOT

    def update_file(self, settings: Settings) -> None:
        self._update_file(settings.input_config.bot_path)

    @classmethod
    def from_issue(cls, issue: Issue) -> "BotPublishInfo":
        return BotPublishInfo()

    def is_valid(self) -> bool:
        return self.homepage_is_valid()


class PluginPublishInfo(PublishInfo):
    """发布插件所需信息"""

    _is_published: Optional[bool] = PrivateAttr()

    module_name: str
    project_link: str

    def get_type(self) -> PublishType:
        return PublishType.PLUGIN

    def update_file(self, settings: Settings) -> None:
        self._update_file(settings.input_config.plugin_path)

    @classmethod
    def from_issue(cls, issue: Issue) -> "PluginPublishInfo":
        return PluginPublishInfo()

    def is_published(self) -> bool:
        if self._is_published is None:
            self._is_published = check_pypi(self.project_link)
        return self._is_published

    def is_valid(self) -> bool:
        return self.is_published and self.homepage_is_valid()


class AdapterPublishInfo(PublishInfo):
    """发布适配器所需信息"""

    module_name: str
    project_link: str

    def get_type(self) -> PublishType:
        return PublishType.ADAPTER

    def update_file(self, settings: Settings) -> None:
        self._update_file(settings.input_config.adapter_path)

    @classmethod
    def from_issue(cls, issue: Issue) -> "AdapterPublishInfo":
        return AdapterPublishInfo()

    def is_published(self) -> bool:
        if self._is_published is None:
            self._is_published = check_pypi(self.project_link)
        return self._is_published

    def is_valid(self) -> bool:
        return self.is_published and self.homepage_is_valid()


def check_pypi(project_link: str) -> bool:
    """检查项目是否存在"""
    url = f"https://pypi.org/pypi/${project_link}/json"
    r = requests.get(url)
    return r.status_code == 200


def check_url(url: str) -> Optional[int]:
    """检查网址是否可以访问

    返回状态码，如果报错则返回 None
    """
    try:
        r = requests.get(url)
        return r.status_code
    except:
        pass


def generate_message(info: PublishInfo) -> str:
    message = f"> {info.get_type().value}: {info.name}"

    if info.is_valid():
        message += "\n\n**✅ All tests passed, you are ready to go!**"
    else:
        message += (
            "\n\n**⚠️ We have found following problem(s) in pre-publish progress:**"
        )

    error_message: list[str] = []
    if info.homepage_status_code != 200:
        error_message.append(
            f"""
            <li>
            ⚠️ Project <a href="{info.homepage}">homepage</a> returns {info.homepage_status_code}.
            <dt>Please make sure that your project has a publicly visible homepage.</dt>
            </li>
            """
        )
    if isinstance(info, AdapterPublishInfo) or isinstance(info, PluginPublishInfo):
        if not info.is_published():
            error_message.append(
                f"""
                <li>
                ⚠️ Package <a href="https://pypi.org/project/{info.project_link}/">{info.project_link}</a> is not available on PyPI.
                <dt>Please publish your package to PyPI.</dt>
                </li>
                """
            )
    if len(error_message) != 0:
        message += f"\n<pre><code>{'\n'.join(error_message)}</code></pre>"

    detail_message: list[str]  = []
    if info.homepage_status_code == 200:
        detail_message.append(f"""
         <li>✅ Project <a href="{info.homepage}">homepage</a> returns ${info.homepage_status_code}.</li>
         """)
    if isinstance(info, AdapterPublishInfo) or isinstance(info, PluginPublishInfo):
        if info.is_published():
            detail_message.append(f"""
            <li>
            ✅ Package <a href="https://pypi.org/project/{info.project_link}/">{info.project_link}</a> is available on PyPI.
            </li>
            """ )
    if len(detail_message) != 0:
        message += f"""
        \n<details>
        <summary>Report Detail</summary>
        <pre><code>${'\n'.join(detail_message)}</code></pre>
        </details>
        """

    return message
