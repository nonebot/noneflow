import abc
import html
import json
import re
from enum import Enum
from typing import Any

from nonebot import logger
from pydantic import BaseModel, root_validator, validator

from src.utils.constants import (
    MAX_NAME_LENGTH,
    PLUGIN_VALID_TYPE,
    PYPI_PACKAGE_NAME_PATTERN,
    PYTHON_MODULE_NAME_REGEX,
)

from .errors import HomepageError
from .utils import check_pypi, check_url, get_adapters, resolve_adapter_name


class PublishType(Enum):
    """发布的类型

    值为标签名
    """

    BOT = "Bot"
    PLUGIN = "Plugin"
    ADAPTER = "Adapter"


class PyPIMixin(BaseModel):
    module_name: str
    project_link: str

    previous_data: list[dict[str, str]]

    @validator("module_name", pre=True)
    def module_name_validator(cls, v: str) -> str:
        if not PYTHON_MODULE_NAME_REGEX.match(v):
            raise ValueError(f"⚠️ 包名 {v} 不符合规范。<dt>请确保包名正确。</dt>")
        return v

    @validator("project_link", pre=True)
    def project_link_validator(cls, v: str) -> str:
        if not PYPI_PACKAGE_NAME_PATTERN.match(v):
            raise ValueError(f"⚠️ PyPI 项目名 {v} 不符合规范。<dt>请确保项目名正确。</dt>")

        if v and not check_pypi(v):
            raise ValueError(
                f'⚠️ 包 <a href="https://pypi.org/project/{v}/">{v}</a> 未发布至 PyPI。<dt>请将您的包发布至 PyPI。</dt>'
            )
        return v

    @root_validator
    def prevent_duplication(cls, values: dict[str, Any]) -> dict[str, Any]:
        module_name = values.get("module_name")
        project_link = values.get("project_link")

        data = values.get("previous_data")
        if data is None:
            raise ValueError("⚠️ 未获取到数据列表。")

        if any(
            map(
                lambda x: x["module_name"] == module_name
                and x["project_link"] == project_link,
                data,
            )
        ):
            raise ValueError(
                f"⚠️ PyPI 项目名 {project_link} 加包名 {module_name} 的值与商店重复。<dt>请确保没有重复发布。</dt>"
            )
        return values


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

    @validator("name", pre=True)
    def name_validator(cls, v: str) -> str:
        if len(v) > MAX_NAME_LENGTH:
            raise ValueError(f"⚠️ 名称过长。<dt>请确保名称不超过 {MAX_NAME_LENGTH} 个字符。</dt>")
        return v

    @validator("homepage", pre=True)
    def homepage_validator(cls, v: str) -> str:
        if v:
            status_code = check_url(v)
            if status_code != 200:
                raise HomepageError(
                    msg=f"项目主页返回状态码 {status_code}。", hint=f"请确保您的项目主页可访问。"
                )
        return v

    @validator("tags", pre=True)
    def tags_validator(cls, v: str) -> list[dict[str, str]]:
        try:
            tags: list[Any] | Any = json.loads(v)
        except json.JSONDecodeError:
            raise ValueError("⚠️ 标签解码失败。<dt>请确保标签为 JSON 格式。</dt>")
        if not isinstance(tags, list):
            raise ValueError("⚠️ 标签格式错误。<dt>请确保标签为列表。</dt>")
        if len(tags) > 0 and any(map(lambda x: not isinstance(x, dict), tags)):
            raise ValueError("⚠️ 标签格式错误。<dt>请确保标签列表内均为字典。</dt>")
        if len(tags) > 3:
            raise ValueError("⚠️ 标签数量过多。<dt>请确保标签数量不超过 3 个。</dt>")
        return tags

    @classmethod
    @abc.abstractmethod
    def get_type(cls) -> PublishType:
        """获取发布类型"""
        raise NotImplementedError


class PluginPublishInfo(PublishInfo, PyPIMixin):
    """发布插件所需信息"""

    type: str
    """插件类型"""
    supported_adapters: list[str] | None
    """插件支持的适配器"""

    skip_plugin_test: bool
    """是否跳过插件测试"""
    plugin_test_result: bool
    """插件测试结果"""
    plugin_test_output: str
    """插件测试输出"""

    @root_validator(pre=True)
    def plugin_test_validator(cls, values) -> bool:
        skip = values.get("skip_plugin_test")
        if skip:
            logger.info("已跳过插件测试")
            return values

        result = values.get("plugin_test_result")
        output = values.get("plugin_test_output")
        if not result:
            raise ValueError(
                f"⚠️ 插件加载测试未通过。<details><summary>测试输出</summary>{html.escape(output)}</details>"
            )
        return values

    @validator("type", pre=True)
    def type_validator(cls, v: str) -> str:
        if not v:
            raise ValueError(f"⚠️ 插件类型不能为空。<dt>请确保填写插件类型。</dt>")

        if v not in PLUGIN_VALID_TYPE:
            raise ValueError(
                f"⚠️ 插件类型 {v} 不符合规范。<dt>请确保插件类型正确，当前仅支持 application 与 library。</dt>"
            )
        return v

    @validator("supported_adapters", pre=True)
    def supported_adapters_validator(cls, v: str | set[str] | None) -> list[str] | None:
        # 如果是从 issue 中获取的数据，需要先解码
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("⚠️ 插件支持的适配器解码失败。<dt>请确保适配器列表为 JSON 格式。</dt>")

        # 如果是支持所有适配器，值应该是 None，不需要检查
        if v is None:
            return None

        if not isinstance(v, (list, set)):
            raise ValueError("⚠️ 适配器列表格式错误。<dt>请确保适配器列表格式无误。</dt>")

        supported_adapters = {resolve_adapter_name(x) for x in v}
        store_adapters = get_adapters()

        missing_adapters = supported_adapters - store_adapters
        if missing_adapters:
            raise ValueError(
                f"⚠️ 适配器 {', '.join(missing_adapters)} 不存在。<dt>请确保适配器模块名称正确。</dt>"
            )
        return sorted(supported_adapters)

    @classmethod
    def get_type(cls) -> PublishType:
        return PublishType.PLUGIN


class AdapterPublishInfo(PublishInfo, PyPIMixin):
    """发布适配器所需信息"""

    @classmethod
    def get_type(cls) -> PublishType:
        return PublishType.ADAPTER


class BotPublishInfo(PublishInfo):
    """发布机器人所需信息"""

    @classmethod
    def get_type(cls) -> PublishType:
        return PublishType.BOT
