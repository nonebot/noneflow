import abc
import json
import logging
import re
from enum import Enum
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

import requests
from pydantic import BaseModel, BaseSettings, SecretStr, ValidationError, validator

from .check_plugin import check_load

if TYPE_CHECKING:
    from github.Issue import Issue
    from pydantic.error_wrappers import ErrorDict

from .constants import (
    ADAPTER_DESC_PATTERN,
    ADAPTER_HOMEPAGE_PATTERN,
    ADAPTER_MODULE_NAME_PATTERN,
    ADAPTER_NAME_PATTERN,
    BOT_DESC_PATTERN,
    BOT_HOMEPAGE_PATTERN,
    BOT_NAME_PATTERN,
    DETAIL_MESSAGE_TEMPLATE,
    PLUGIN_DESC_PATTERN,
    PLUGIN_HOMEPAGE_PATTERN,
    PLUGIN_MODULE_NAME_PATTERN,
    PLUGIN_NAME_PATTERN,
    PROJECT_LINK_PATTERN,
    TAGS_PATTERN,
    VALIDATION_MESSAGE_TEMPLATE,
)


class MyValidationError(ValueError):
    """验证错误错误"""

    def __init__(
        self,
        type: "PublishType",
        raw_data: dict[str, Any],
        errors: list["ErrorDict"],
    ) -> None:
        self.type = type
        self.raw_data = raw_data
        self.errors = errors

    @property
    def message(self) -> str:
        return generate_validation_message(self)


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
            raise ValueError("标签名称过长<dt>请确保标签名称不超过 10 个字符。</dt>")
        return v

    @validator("color", pre=True)
    def color_validator(cls, v: str) -> str:
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("标签颜色错误<dt>请确保标签颜色符合十六进制颜色码规则。</dt>")
        return v


class PublishInfo(abc.ABC, BaseModel):
    """发布信息"""

    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Tag]
    is_official: bool = False

    @validator("homepage", pre=True)
    def homepage_validator(cls, v: str) -> str:
        status_code = check_url(v)
        if status_code != 200:
            raise ValueError(
                f"""⚠️ 项目 <a href="{v}">主页</a> 返回状态码 {status_code}。<dt>请确保您的项目主页可访问。</dt>"""
            )
        return v

    @validator("tags", pre=True)
    def tags_validator(cls, v: str) -> list[dict[str, str]]:
        try:
            tags: Union[list[dict[str, str]], Any] = json.loads(v)
        except json.JSONDecodeError:
            raise ValueError("⚠️ 标签解码失败。<dt>请确保标签格式正确。</dt>")
        if not isinstance(tags, list):
            raise ValueError("⚠️ 标签格式错误。<dt>请确保标签为列表。</dt>")
        if len(tags) > 3:
            raise ValueError("⚠️ 标签数量过多。<dt>请确保标签数量不超过 3 个。</dt>")
        return tags

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
    def from_issue(self, issue: "Issue") -> "PublishInfo":
        """从议题中获取所需信息"""
        raise NotImplementedError

    @classmethod
    @abc.abstractclassmethod
    def get_type(cls) -> PublishType:
        """获取发布类型"""
        raise NotImplementedError

    @property
    def validation_message(self) -> str:
        """验证信息"""
        return generate_validation_message(self)


class PyPIMixin(BaseModel):
    project_link: str
    module_name: str

    @validator("project_link", pre=True)
    def project_link_validator(cls, v: str) -> str:
        if not check_pypi(v):
            raise ValueError(
                f'⚠️ 包 <a href="https://pypi.org/project/{v}/">{v}</a> 未发布至 PyPI。<dt>请将您的包发布至 PyPI。</dt>'
            )
        return v


class BotPublishInfo(PublishInfo):
    """发布机器人所需信息"""

    @classmethod
    def get_type(cls) -> PublishType:
        return PublishType.BOT

    def update_file(self, settings: Settings) -> None:
        self._update_file(settings.input_config.bot_path)

    @classmethod
    def from_issue(cls, issue: "Issue") -> "BotPublishInfo":
        body = issue.body

        name = BOT_NAME_PATTERN.search(body)
        desc = BOT_DESC_PATTERN.search(body)
        author = issue.user.login
        homepage = BOT_HOMEPAGE_PATTERN.search(body)
        tags = TAGS_PATTERN.search(body)

        if not (name and desc and author and homepage and tags):
            raise ValueError("无法获取机器人信息")

        raw_data = {
            "name": name.group(1).strip(),
            "desc": desc.group(1).strip(),
            "author": author,
            "homepage": homepage.group(1).strip(),
            "tags": tags.group(1).strip(),
        }

        try:
            return BotPublishInfo(**raw_data)  # type: ignore
        except ValidationError as e:
            raise MyValidationError(cls.get_type(), raw_data, e.errors())


class PluginPublishInfo(PublishInfo, PyPIMixin):
    """发布插件所需信息"""

    @validator("module_name", pre=True)
    def plugin_load_validator(cls, module_name: str, values: dict[str, str]):
        project_link = values.get("project_link", "")
        if message := check_load(project_link, module_name):
            raise ValueError(f"⚠️ 插件加载失败: {message}。<dt>请确保插件能成功加载。</dt>")
        return module_name

    @classmethod
    def get_type(cls) -> PublishType:
        return PublishType.PLUGIN

    def update_file(self, settings: Settings) -> None:
        self._update_file(settings.input_config.plugin_path)

    @classmethod
    def from_issue(cls, issue: "Issue") -> "PluginPublishInfo":
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

        raw_data = {
            "project_link": project_link.group(1).strip(),
            "module_name": module_name.group(1).strip(),
            "name": name.group(1).strip(),
            "desc": desc.group(1).strip(),
            "author": author,
            "homepage": homepage.group(1).strip(),
            "tags": tags.group(1).strip(),
        }

        try:
            return PluginPublishInfo(**raw_data)  # type: ignore
        except ValidationError as e:
            raise MyValidationError(cls.get_type(), raw_data, e.errors())


class AdapterPublishInfo(PublishInfo, PyPIMixin):
    """发布适配器所需信息"""

    @classmethod
    def get_type(cls) -> PublishType:
        return PublishType.ADAPTER

    def update_file(self, settings: Settings) -> None:
        self._update_file(settings.input_config.adapter_path)

    @classmethod
    def from_issue(cls, issue: "Issue") -> "AdapterPublishInfo":
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

        raw_data = {
            "project_link": project_link.group(1).strip(),
            "module_name": module_name.group(1).strip(),
            "name": name.group(1).strip(),
            "desc": desc.group(1).strip(),
            "author": author,
            "homepage": homepage.group(1).strip(),
            "tags": tags.group(1).strip(),
        }

        try:
            return AdapterPublishInfo(**raw_data)  # type: ignore
        except ValidationError as e:
            raise MyValidationError(cls.get_type(), raw_data, e.errors())


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


def generate_validation_message(info: Union[PublishInfo, MyValidationError]) -> str:
    """生成验证信息"""
    if isinstance(info, MyValidationError):
        # 如果有错误
        publish_info: str = f"{info.type.value}: {info.raw_data['name']}"
        result = "⚠️ 在发布检查过程中，我们发现以下问题:"

        errors: list[str] = []
        for error in info.errors:
            if error["loc"][0] == "tags" and len(error["loc"]) == 3:
                if error["type"] == "value_error.missing":
                    errors.append(
                        f"<li>⚠️ 第 {error['loc'][1]+1} 个标签缺少 {error['loc'][2]} 字段。<dt>请确保标签字段完整。</dt></li>"  # type: ignore
                    )
                else:
                    errors.append(f"<li>⚠️ 第 {error['loc'][1]+1} 个{error['msg']}</li>")  # type: ignore
            else:
                errors.append(f"<li>{error['msg']}</li>")

        error_message = "".join(errors)
        error_message = f"<pre><code>{error_message}</code></pre>"
    else:
        # 一切正常时
        publish_info = f"{info.get_type().value}: {info.name}"
        result = "✅ 所有测试通过，一切准备就绪!"
        error_message = ""

    detail_message = ""
    details: list[str] = []

    # 验证失败的项
    error_keys = (
        [error["loc"][0] for error in info.errors]
        if isinstance(info, MyValidationError)
        else []
    )

    # 标签
    tags = []
    if isinstance(info, PublishInfo):
        tags = [f"{tag.label}-{tag.color}" for tag in info.tags]
    elif "tags" not in error_keys:
        # 原始 tags 为 json 字符串
        # 需要先转换才能读取
        tags = [
            f"{tag['label']}-{tag['color']}"
            for tag in json.loads(info.raw_data["tags"])
        ]

    if tags:
        details.append(f"<li>✅ 标签: {', '.join(tags)}</li>")

    # 主页
    homepage = ""
    if isinstance(info, PublishInfo):
        homepage = info.homepage
    elif "homepage" not in error_keys:
        homepage = info.raw_data["homepage"]
    if homepage:
        details.append(
            f"""<li>✅ 项目 <a href="{homepage}">主页</a> 返回状态码 {check_url(homepage)}.</li>"""
        )

    # 发布情况
    project_link = ""
    if isinstance(info, AdapterPublishInfo) or isinstance(info, PluginPublishInfo):
        project_link = info.project_link
    elif (
        isinstance(info, MyValidationError)
        and info.type in [PublishType.PLUGIN, PublishType.ADAPTER]
        and "project_link" not in error_keys
    ):
        project_link = info.raw_data["project_link"]
    if project_link:
        details.append(
            f"""<li>✅ 包 <a href="https://pypi.org/project/{project_link}/">{project_link}</a> 已发布至 PyPI</li>"""
        )

    # 插件加载情况
    module_name = ""
    if isinstance(info, PluginPublishInfo) and info.get_type() == PublishType.PLUGIN:
        module_name = info.module_name
    elif (
        isinstance(info, MyValidationError)
        and info.type == PublishType.PLUGIN
        and "module_name" not in error_keys
    ):
        module_name = info.raw_data["module_name"]
    if module_name:
        details.append(f"""<li>✅ 插件 {module_name} 加载成功</li>""")

    if len(details) != 0:
        detail_message = "".join(details)
        detail_message = DETAIL_MESSAGE_TEMPLATE.format(detail_message=detail_message)

    return VALIDATION_MESSAGE_TEMPLATE.format(
        publish_info=publish_info,
        result=result,
        error_message=error_message,
        detail_message=detail_message,
    ).strip()
