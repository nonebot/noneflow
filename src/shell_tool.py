import logging
import subprocess


def run_shell_command(command: list[str]):
    """运行 shell 命令

    如果遇到错误则抛出异常
    """
    logging.info(f"运行命令: {command}")
    subprocess.run(command, check=True, capture_output=True)
