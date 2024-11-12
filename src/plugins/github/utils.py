import subprocess
from re import Pattern

from nonebot import logger


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


def extract_issue_info_from_issue(
    patterns: dict[str, Pattern[str]], body: str
) -> dict[str, str | None]:
    """
    根据提供的正则表达式和议题内容来提取所需的信息
    """
    matchers = {key: pattern.search(body) for key, pattern in patterns.items()}
    # 如果未匹配到数据，则不添加进字典中
    # 这样可以让 Pydantic 在校验时报错 missing
    data = {key: match.group(1).strip() for key, match in matchers.items() if match}
    return data
