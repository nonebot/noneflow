""" 检查插件 """
import logging
import os
import sys
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional

from platformdirs import user_cache_dir

from .shell_tool import run_shell_command

BASE_CACHE_DIR = Path(user_cache_dir("publish_bot"))

RUNNER = """import sys
from nonebot import get_driver, init, load_plugin
from nonebot.log import default_filter, default_format, logger
init()

logger.remove()
logger.add(
    sys.stdout,
    level=0,
    colorize=False,
    diagnose=False,
    filter=default_filter,
    format=default_format,
)

valid = load_plugin("{}")
if not valid:
    exit(1)
"""


def check_load(project_link: str, module_name: str) -> Optional[str]:
    """检查插件是否能正常加载"""
    logging.info(f"检查插件 {project_link=}, {module_name=}")
    if not project_link or not module_name:
        return "项目信息不全"

    os.makedirs(BASE_CACHE_DIR, exist_ok=True)
    with open(BASE_CACHE_DIR / "runner.py", "w") as f:
        f.write(RUNNER.format(module_name))

    if sys.platform == "win32":
        python_path = f"{BASE_CACHE_DIR}/venv/Scripts/python"
    else:
        python_path = f"{BASE_CACHE_DIR}/venv/bin/python"

    # 设置虚拟环境
    run_shell_command(["python", "-m", "venv", f"{BASE_CACHE_DIR}/venv"])

    # 安装插件
    try:
        logging.info("正在安装插件")
        run_shell_command(
            [
                python_path,
                "-m",
                "pip",
                "install",
                project_link,
            ]
        )
    except CalledProcessError as e:
        logging.info("插件安装失败")
        logging.info(e.output.decode())
        logging.info(e.stderr.decode())
        return "插件安装失败"

    # 加载插件
    try:
        logging.info("正在加载插件")
        run_shell_command([python_path, f"{BASE_CACHE_DIR}/runner.py"])
    except CalledProcessError as e:
        logging.info("加载插件失败")
        output = e.output.decode()
        logging.info(output)
        return output.splitlines()[-1]
