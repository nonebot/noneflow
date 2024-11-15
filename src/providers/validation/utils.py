from functools import cache
from typing import TYPE_CHECKING

import httpx

from providers.utils import load_json_from_web
from src.providers.constants import STORE_ADAPTERS_URL

from .constants import MESSAGE_TRANSLATIONS

if TYPE_CHECKING:
    from pydantic_core import ErrorDetails


@cache
def get_url(url: str) -> httpx.Response:
    """获取网址"""
    return httpx.get(url, follow_redirects=True)


def get_pypi_name(project_link: str) -> str:
    """获取 PyPI 项目名"""
    url = f"https://pypi.org/pypi/{project_link}/json"
    r = get_url(url)
    r.raise_for_status()
    data = r.json()
    return data["info"]["name"]


def get_upload_time(project_link: str) -> str | None:
    """获取插件的上传时间"""
    url = f"https://pypi.org/pypi/{project_link}/json"
    r = get_url(url)
    if r.status_code != 200:
        return None
    try:
        data = r.json()
    except Exception:
        return None
    return data["urls"][0]["upload_time_iso_8601"]


def check_pypi(project_link: str) -> bool:
    """检查项目是否存在"""
    url = f"https://pypi.org/pypi/{project_link}/json"
    status_code, _ = check_url(url)
    return status_code == 200


def check_url(url: str) -> tuple[int, str]:
    """检查网址是否可以访问

    返回状态码，如果报错则返回 -1
    """
    try:
        r = get_url(url)
        return r.status_code, ""
    except Exception as e:
        return -1, str(e)


@cache
def get_author_name(author_id: int) -> str:
    """通过作者的ID获取作者名字"""
    url = f"https://api.github.com/user/{author_id}"
    return load_json_from_web(url)["login"]


def get_adapters() -> set[str]:
    """获取适配器列表"""
    adapters = load_json_from_web(STORE_ADAPTERS_URL)
    return {adapter["module_name"] for adapter in adapters}


def resolve_adapter_name(name: str) -> str:
    """解析适配器名称

    例如：`~onebot.v11` -> `nonebot.adapters.onebot.v11`
    """
    if name.startswith("~"):
        name = "nonebot.adapters." + name[1:]
    return name


def translate_errors(errors: list["ErrorDetails"]) -> list["ErrorDetails"]:
    """翻译 Pydantic 错误信息"""
    new_errors: list["ErrorDetails"] = []
    for error in errors:
        translation = MESSAGE_TRANSLATIONS.get(error["type"])
        if translation:
            ctx = error.get("ctx")
            error["msg"] = translation.format(**ctx) if ctx else translation
        new_errors.append(error)
    return new_errors
