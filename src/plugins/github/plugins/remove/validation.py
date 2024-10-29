from githubkit.rest import Issue
from nonebot import logger
from pydantic_core import PydanticCustomError

from src.plugins.github.models import AuthorInfo
from src.plugins.github.utils import extract_publish_info_from_issue

from .constants import PUBLISH_PATH, REMOVE_HOMEPAGE_PATTERN
from .utils import RemoveInfo, load_json


async def validate_author_info(issue: Issue) -> RemoveInfo:
    """
    根据主页链接与作者信息找到对应的包的信息
    """

    homepage = extract_publish_info_from_issue(
        {"homepage": REMOVE_HOMEPAGE_PATTERN}, issue.body or ""
    ).get("homepage")
    author_id = AuthorInfo.from_issue(issue).author_id

    if homepage is None:
        raise PydanticCustomError("not_homepage", "主页链接未填写")

    for type, path in PUBLISH_PATH.items():
        if not path.exists():
            logger.info(f"{type} 数据文件不存在，跳过")
            continue

        data: list[dict[str, str]] = load_json(path)
        for item in data:
            if item.get("homepage") == homepage:
                logger.info(f"找到匹配的 {type} 数据 {item}")

                # author_id 暂时没有储存到数据里, 所以暂时不校验
                if item.get("author_id") == author_id:
                    return RemoveInfo(
                        type=type,
                        name=item.get("name") or item.get("module_name") or "",
                        homepage=homepage,
                        author_id=author_id,
                    )
                raise PydanticCustomError("author_info", "作者信息不匹配")
    raise PydanticCustomError("not_found", "没有包含对应主页链接的包")
