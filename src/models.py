import abc
import json
import logging
import re
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Optional

import requests
from github.Issue import Issue
from pydantic import BaseModel, BaseSettings, SecretStr, validator

from .constants import (
    ADAPTER_DESC_PATTERN,
    ADAPTER_HOMEPAGE_PATTERN,
    ADAPTER_MODULE_NAME_PATTERN,
    ADAPTER_NAME_PATTERN,
    BOT_DESC_PATTERN,
    BOT_HOMEPAGE_PATTERN,
    BOT_NAME_PATTERN,
    PLUGIN_DESC_PATTERN,
    PLUGIN_HOMEPAGE_PATTERN,
    PLUGIN_MODULE_NAME_PATTERN,
    PLUGIN_NAME_PATTERN,
    PROJECT_LINK_PATTERN,
    TAGS_PATTERN,
    VALIDATION_MESSAGE_TEMPLATE,
)


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


class Tag(BaseModel):
    """标签"""

    label: str
    color: str

    @validator("label", pre=True)
    def label_validator(cls, v: str) -> str:
        if len(v) > 10:
            raise ValueError("标签名称不能超过 10 个字符")
        return v

    @validator("color", pre=True)
    def color_validator(cls, v: str) -> str:
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("颜色不符合规则")
        return v


class PublishInfo(abc.ABC, BaseModel):
    """发布信息"""

    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: bool = False

    @validator("tags", pre=True)
    def tags_validator(cls, v: list[Tag]) -> list[Tag]:
        if len(v) > 3:
            raise ValueError("标签数量不能超过 3 个")
        return v

    def _update_file(self, path: Path):
        logging.info(f"正在更新文件: {path}")
        with path.open("r", encoding="utf-8") as f:
            data: list[dict[str, str]] = json.load(f)
        with path.open("w", encoding="utf-8") as f:
            data.append(self.dict())
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"文件更新完成")

    @abc.abstractmethod
    def update_file(self, settings: Settings) -> None:
        """更新文件"""
        raise NotImplementedError

    @abc.abstractmethod
    def from_issue(self, issue: Issue) -> "PublishInfo":
        """从议题中获取所需信息"""
        raise NotImplementedError

    @abc.abstractmethod
    def get_type(self) -> PublishType:
        """获取发布类型"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def is_valid(self) -> bool:
        """检查是否满足要求"""
        raise NotImplementedError

    @property
    def homepage_status_code(self) -> Optional[int]:
        """主页状态码"""
        return check_url(self.homepage)

    @property
    def is_homepage_valid(self) -> bool:
        """主页是否可用"""
        return self.homepage_status_code == 200

    @property
    def validation_message(self) -> str:
        """验证信息"""
        return generate_validation_message(self)


class PyPIMixin(BaseModel):
    module_name: str
    project_link: str

    @property
    def is_published(self) -> bool:
        return check_pypi(self.project_link)


class BotPublishInfo(PublishInfo):
    """发布机器人所需信息"""

    def get_type(self) -> PublishType:
        return PublishType.BOT

    def update_file(self, settings: Settings) -> None:
        self._update_file(settings.input_config.bot_path)

    @classmethod
    def from_issue(cls, issue: Issue) -> "BotPublishInfo":
        body = issue.body

        name = BOT_NAME_PATTERN.search(body)
        desc = BOT_DESC_PATTERN.search(body)
        author = issue.user.login
        homepage = BOT_HOMEPAGE_PATTERN.search(body)
        tags = TAGS_PATTERN.search(body)

        if not (name and desc and author and homepage and tags):
            raise ValueError("无法获取机器人信息")

        return BotPublishInfo(
            name=name.group(1).strip(),
            desc=desc.group(1).strip(),
            author=author,
            homepage=homepage.group(1).strip(),
            tags=json.loads(tags.group(1).strip()),
        )

    @property
    def is_valid(self) -> bool:
        return self.is_homepage_valid


class PluginPublishInfo(PublishInfo, PyPIMixin):
    """发布插件所需信息"""

    def get_type(self) -> PublishType:
        return PublishType.PLUGIN

    def update_file(self, settings: Settings) -> None:
        self._update_file(settings.input_config.plugin_path)

    @classmethod
    def from_issue(cls, issue: Issue) -> "PluginPublishInfo":
        body = issue.body

        module_name = PLUGIN_MODULE_NAME_PATTERN.search(body)
        project_link = PROJECT_LINK_PATTERN.search(body)
        name = PLUGIN_NAME_PATTERN.search(body)
        desc = PLUGIN_DESC_PATTERN.search(body)
        author = issue.user.login
        homepage = PLUGIN_HOMEPAGE_PATTERN.search(body)
        tags = TAGS_PATTERN.search(body)

        if not (
            module_name
            and project_link
            and name
            and desc
            and author
            and homepage
            and tags
        ):
            raise ValueError("无法获取插件信息")

        return PluginPublishInfo(
            module_name=module_name.group(1).strip(),
            project_link=project_link.group(1).strip(),
            name=name.group(1).strip(),
            desc=desc.group(1).strip(),
            author=author,
            homepage=homepage.group(1).strip(),
            tags=json.loads(tags.group(1).strip()),
        )

    @property
    def is_valid(self) -> bool:
        return self.is_published and self.is_homepage_valid


class AdapterPublishInfo(PublishInfo, PyPIMixin):
    """发布适配器所需信息"""

    def get_type(self) -> PublishType:
        return PublishType.ADAPTER

    def update_file(self, settings: Settings) -> None:
        self._update_file(settings.input_config.adapter_path)

    @classmethod
    def from_issue(cls, issue: Issue) -> "AdapterPublishInfo":
        body = issue.body

        module_name = ADAPTER_MODULE_NAME_PATTERN.search(body)
        project_link = PROJECT_LINK_PATTERN.search(body)
        name = ADAPTER_NAME_PATTERN.search(body)
        desc = ADAPTER_DESC_PATTERN.search(body)
        author = issue.user.login
        homepage = ADAPTER_HOMEPAGE_PATTERN.search(body)
        tags = TAGS_PATTERN.search(body)

        if not (
            module_name
            and project_link
            and name
            and desc
            and author
            and homepage
            and tags
        ):
            raise ValueError("无法获取适配器信息")

        return AdapterPublishInfo(
            module_name=module_name.group(1).strip(),
            project_link=project_link.group(1).strip(),
            name=name.group(1).strip(),
            desc=desc.group(1).strip(),
            author=author,
            homepage=homepage.group(1).strip(),
            tags=json.loads(tags.group(1).strip()),
        )

    @property
    def is_valid(self) -> bool:
        return self.is_published and self.is_homepage_valid


def check_pypi(project_link: str) -> bool:
    """检查项目是否存在"""
    url = f"https://pypi.org/pypi/{project_link}/json"
    status_code = check_url(url)
    return status_code == 200


@cache
def check_url(url: str) -> Optional[int]:
    """检查网址是否可以访问

    返回状态码，如果报错则返回 None
    """
    logging.info(f"检查网址 {url}")
    try:
        r = requests.get(url)
        return r.status_code
    except:
        pass


def generate_validation_message(info: PublishInfo) -> str:
    """生成验证信息"""
    publish_info = f"{info.get_type().value}: {info.name}"

    if info.is_valid:
        result = "✅ All tests passed, you are ready to go!"
    else:
        result = "⚠️ We have found following problem(s) in pre-publish progress:"

    error_message = ""
    errors: list[str] = []
    if info.homepage_status_code != 200:
        errors.append(
            f"""<li>⚠️ Project <a href="{info.homepage}">homepage</a> returns {info.homepage_status_code}.<dt>Please make sure that your project has a publicly visible homepage.</dt></li>"""
        )
    if isinstance(info, AdapterPublishInfo) or isinstance(info, PluginPublishInfo):
        if not info.is_published:
            errors.append(
                f"""<li>⚠️ Package <a href="https://pypi.org/project/{info.project_link}/">{info.project_link}</a> is not available on PyPI.<dt>Please publish your package to PyPI.</dt></li>"""
            )
    if len(errors) != 0:
        error_message = "".join(errors)
        error_message = f"<pre><code>{error_message}</code></pre>"

    detail_message = ""
    details: list[str] = []
    if info.homepage_status_code == 200:
        details.append(
            f"""<li>✅ Project <a href="{info.homepage}">homepage</a> returns {info.homepage_status_code}.</li>"""
        )
    if isinstance(info, AdapterPublishInfo) or isinstance(info, PluginPublishInfo):
        if info.is_published:
            details.append(
                f"""<li>✅ Package <a href="https://pypi.org/project/{info.project_link}/">{info.project_link}</a> is available on PyPI.</li>"""
            )
    if len(details) != 0:
        detail_message = "".join(details)
        detail_message = f"""<details><summary>Report Detail</summary><pre><code>{detail_message}</code></pre></details>"""

    return VALIDATION_MESSAGE_TEMPLATE.format(
        publish_info=publish_info,
        result=result,
        error_message=error_message,
        detail_message=detail_message,
    ).strip()
