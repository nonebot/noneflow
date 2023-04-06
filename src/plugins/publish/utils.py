import logging
import re
import subprocess
from typing import TYPE_CHECKING, Union

from .constants import BRANCH_NAME_PREFIX, COMMIT_MESSAGE_PREFIX
from .models import PublishType
from .validation import (
    AdapterPublishInfo,
    BotPublishInfo,
    MyValidationError,
    PluginPublishInfo,
    PublishInfo,
)

if TYPE_CHECKING:
    from githubkit.rest.models import Issue, IssuePropLabelsItemsOneof1, Label
    from githubkit.webhooks.models import Issue as WebhookIssue
    from githubkit.webhooks.models import (
        IssueCommentCreatedPropIssue,
        IssuesOpenedPropIssue,
        IssuesReopenedPropIssue,
    )
    from githubkit.webhooks.models import Label as WebhookLabel


def run_shell_command(command: list[str]):
    """运行 shell 命令

    如果遇到错误则抛出异常
    """
    logging.info(f"运行命令: {command}")
    try:
        r = subprocess.run(command, check=True, capture_output=True)
        logging.debug(f"命令输出: \n{r.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logging.debug("命令运行失败")
        logging.debug(f"命令输出: \n{e.stdout.decode()}")
        logging.debug(f"命令错误: \n{e.stderr.decode()}")
        raise
    return r


def get_type_by_labels(
    labels: list["Label"]
    | list["WebhookLabel"]
    | list[Union[str, "IssuePropLabelsItemsOneof1"]],
) -> PublishType | None:
    """通过标签获取类型"""
    for label in labels:
        if isinstance(label, str):
            continue
        if label.name == PublishType.BOT.value:
            return PublishType.BOT
        if label.name == PublishType.PLUGIN.value:
            return PublishType.PLUGIN
        if label.name == PublishType.ADAPTER.value:
            return PublishType.ADAPTER


def get_type_by_title(title: str) -> PublishType | None:
    """通过标题获取类型"""
    if title.startswith(f"{PublishType.BOT.value}:"):
        return PublishType.BOT
    if title.startswith(f"{PublishType.PLUGIN.value}:"):
        return PublishType.PLUGIN
    if title.startswith(f"{PublishType.ADAPTER.value}:"):
        return PublishType.ADAPTER


def get_type_by_commit_message(message: str) -> PublishType | None:
    """通过提交信息获取类型"""
    if message.startswith(f"{COMMIT_MESSAGE_PREFIX} {PublishType.BOT.value.lower()}"):
        return PublishType.BOT
    if message.startswith(
        f"{COMMIT_MESSAGE_PREFIX} {PublishType.PLUGIN.value.lower()}"
    ):
        return PublishType.PLUGIN
    if message.startswith(
        f"{COMMIT_MESSAGE_PREFIX} {PublishType.ADAPTER.value.lower()}"
    ):
        return PublishType.ADAPTER


def commit_and_push(info: PublishInfo, branch_name: str, issue_number: int):
    """提交并推送"""
    commit_message = f"{COMMIT_MESSAGE_PREFIX} {info.get_type().value.lower()} {info.name} (#{issue_number})"

    run_shell_command(["git", "config", "--global", "user.name", info.author])
    user_email = f"{info.author}@users.noreply.github.com"
    run_shell_command(["git", "config", "--global", "user.email", user_email])
    run_shell_command(["git", "add", "-A"])
    run_shell_command(["git", "commit", "-m", commit_message])

    try:
        run_shell_command(["git", "fetch", "origin"])
        result = run_shell_command(
            ["git", "diff", f"origin/{branch_name}", branch_name]
        )
        if result.stdout:
            raise Exception
        else:
            logging.info("检测到本地分支与远程分支一致，跳过推送")
    except:
        logging.info("检测到本地分支与远程分支不一致，尝试强制推送")
        run_shell_command(["git", "push", "origin", branch_name, "-f"])


def extract_issue_number_from_ref(ref: str) -> int | None:
    """从 Ref 中提取议题号"""
    match = re.search(rf"{BRANCH_NAME_PREFIX}(\d+)", ref)
    if match:
        return int(match.group(1))


def extract_publish_info_from_issue(
    issue: "IssuesOpenedPropIssue | IssuesReopenedPropIssue | IssueCommentCreatedPropIssue | Issue | WebhookIssue",
    publish_type: PublishType,
) -> PublishInfo | MyValidationError:
    """从议题中提取发布所需数据"""
    try:
        if publish_type == PublishType.BOT:
            return BotPublishInfo.from_issue(issue)
        elif publish_type == PublishType.PLUGIN:
            return PluginPublishInfo.from_issue(issue)
        return AdapterPublishInfo.from_issue(issue)
    except MyValidationError as e:
        return e
