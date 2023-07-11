from functools import cache

import httpx
from nonebot import logger

from src.utils.constants import STORE_ADAPTERS_URL


def check_pypi(project_link: str) -> bool:
    """检查项目是否存在"""
    url = f"https://pypi.org/pypi/{project_link}/json"
    status_code = check_url(url)
    return status_code == 200


@cache
def check_url(url: str) -> int | None:
    """检查网址是否可以访问

    返回状态码，如果报错则返回 None
    """
    logger.info(f"检查网址 {url}")
    try:
        r = httpx.get(url)
        return r.status_code
    except:
        pass


loc_map = {
    "name": "名称",
    "desc": "功能",
    "project_link": "PyPI 项目名",
    "module_name": "import 包名",
    "tags": "标签",
    "homepage": "项目仓库/主页链接",
}


def loc_to_name(loc: str) -> str:
    """将 loc 转换为可读名称"""
    if loc in loc_map:
        return loc_map[loc]
    return loc


def get_adapters() -> set[str]:
    """获取适配器列表"""
    resp = httpx.get(STORE_ADAPTERS_URL)
    adapters = resp.json()
    return {adapter["module_name"] for adapter in adapters}


def resolve_adapter_name(name: str) -> str:
    """解析适配器名称

    例如：`~onebot.v11` -> `nonebot.adapters.onebot.v11`
    """
    if name.startswith("~"):
        name = "nonebot.adapters." + name[1:]
    return name
