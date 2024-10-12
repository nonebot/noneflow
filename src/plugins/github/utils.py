import json
import subprocess

from pathlib import Path
from re import Pattern
from typing import Any
from nonebot import logger

from pydantic_core import to_jsonable_python
from githubkit.rest import Issue

from src.plugins.github.typing import AuthorInfo


def run_shell_command(command: list[str]):
    """运行 shell 命令

    如果遇到错误则抛出异常
    """
    logger.info(f"运行命令: {command}")
    try:
        r = subprocess.run(command, check=True, capture_output=True)
        logger.debug(f"命令输出: \n{r.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logger.debug("命令运行失败")
        logger.debug(f"命令输出: \n{e.stdout.decode()}")
        logger.debug(f"命令错误: \n{e.stderr.decode()}")
        raise
    return r


def commit_message(prefix: str, message: str, issue_number: int):
    """生成提交信息"""
    return f"{prefix} {message} (#{issue_number})"


def load_json(path: Path) -> list[dict[str, str]]:
    """加载 JSON 文件"""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, data: Any, indent: int = 4):
    """保存 JSON 文件"""
    with path.open("w", encoding="utf-8") as f:
        # 结尾加上换行符，不然会被 pre-commit fix
        json.dump(to_jsonable_python(data), f, ensure_ascii=False, indent=indent)
        f.write("\n")


def extract_publish_info_from_issue(
    patterns: dict[str, Pattern[str]], body: str
) -> dict[str, str | None]:
    """
    根据提供的正则表达式和议题内容来提取所需的信息
    """
    matchers = {key: pattern.search(body) for key, pattern in patterns.items()}
    data = {
        key: match.group(1).strip() if match else None
        for key, match in matchers.items()
    }
    return data


def extract_author_info(issue: Issue) -> AuthorInfo:
    """
    从议题中获取作者信息
    """
    return {
        "author": issue.user.login if issue.user else "",
        "author_id": issue.user.id if issue.user else 0,
    }
