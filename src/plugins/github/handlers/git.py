from nonebot import logger
from pydantic import BaseModel

from src.plugins.github.utils import run_shell_command


class GitHandler(BaseModel):
    """Git 操作"""

    def checkout_branch(self, branch_name: str):
        """检出分支"""

        run_shell_command(["git", "checkout", branch_name])

    def update_branch(self, branch_name: str):
        """更新本地分支"""

        run_shell_command(["git", "pull", "origin", branch_name])

    def checkout_remote_branch(self, branch_name: str):
        """检出远程分支"""

        run_shell_command(["git", "fetch", "origin", branch_name])
        run_shell_command(["git", "checkout", branch_name])

    def commit_and_push(self, message: str, branch_name: str, author: str):
        """提交并推送"""

        run_shell_command(["git", "config", "--global", "user.name", author])
        user_email = f"{author}@users.noreply.github.com"
        run_shell_command(["git", "config", "--global", "user.email", user_email])
        run_shell_command(["git", "add", "-A"])
        run_shell_command(["git", "commit", "-m", message])
        try:
            run_shell_command(["git", "fetch", "origin"])
            r = run_shell_command(["git", "diff", f"origin/{branch_name}", branch_name])
            if r.stdout:
                raise Exception
            else:
                logger.info("检测到本地分支与远程分支一致，跳过推送")
        except Exception:
            logger.info("检测到本地分支与远程分支不一致，尝试强制推送")
            run_shell_command(["git", "push", "origin", branch_name, "-f"])

    def remote_branch_exists(self, branch_name: str) -> bool:
        """检查远程分支是否存在"""
        result = run_shell_command(
            ["git", "ls-remote", "--heads", "origin", branch_name]
        )
        return bool(result.stdout.decode().strip())

    def delete_remote_branch(self, branch_name: str):
        """删除远程分支"""

        run_shell_command(["git", "push", "origin", "--delete", branch_name])

    def switch_branch(self, branch_name: str):
        """切换分支"""

        run_shell_command(["git", "switch", "-C", branch_name])
