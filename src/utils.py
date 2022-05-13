import logging
import re
import subprocess
from typing import TYPE_CHECKING, Optional, Union

import src.globals as g

from .constants import (
    BRANCH_NAME_PREFIX,
    COMMENT_MESSAGE_TEMPLATE,
    COMMENT_TITLE,
    COMMIT_MESSAGE_PREFIX,
    POWERED_BY_BOT_MESSAGE,
    PUBLISH_BOT_MARKER,
    REUSE_MESSAGE,
)
from .models import (
    AdapterPublishInfo,
    BotPublishInfo,
    MyValidationError,
    PluginPublishInfo,
    PublishInfo,
    PublishType,
)

if TYPE_CHECKING:
    from github.Issue import Issue
    from github.Label import Label
    from github.PullRequest import PullRequest
    from github.Repository import Repository


def run_shell_command(command: list[str]):
    """运行 shell 命令

    如果遇到错误则抛出异常
    """
    logging.info(f"运行命令: {command}")
    subprocess.run(command, check=True)


def get_type_by_labels(labels: list["Label"]) -> Optional[PublishType]:
    """通过标签获取类型"""
    for label in labels:
        if label.name == PublishType.BOT.value:
            return PublishType.BOT
        if label.name == PublishType.PLUGIN.value:
            return PublishType.PLUGIN
        if label.name == PublishType.ADAPTER.value:
            return PublishType.ADAPTER


def get_type_by_title(title: str) -> Optional[PublishType]:
    """通过标题获取类型"""
    if title.startswith(f"{PublishType.BOT.value}:"):
        return PublishType.BOT
    if title.startswith(f"{PublishType.PLUGIN.value}:"):
        return PublishType.PLUGIN
    if title.startswith(f"{PublishType.ADAPTER.value}:"):
        return PublishType.ADAPTER


def get_type_by_commit_message(message: str) -> Optional[PublishType]:
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


def commit_and_push(info: PublishInfo, branch_name: str):
    """提交并推送"""
    commit_message = (
        f"{COMMIT_MESSAGE_PREFIX} {info.get_type().value.lower()} {info.name}"
    )
    run_shell_command(["git", "config", "--global", "user.name", info.author])
    user_email = f"{info.author}@users.noreply.github.com"
    run_shell_command(["git", "config", "--global", "user.email", user_email])
    run_shell_command(["git", "add", "-A"])
    run_shell_command(["git", "commit", "-m", commit_message])
    run_shell_command(["git", "push", "origin", branch_name, "-f"])


def create_pull_request(
    repo: "Repository",
    info: PublishInfo,
    base: str,
    branch_name: str,
    issue_number: int,
):
    """创建拉取请求

    同时添加对应标签
    内容关联上对应的议题
    """
    title = f"{info.get_type().value}: {info.name}"
    # 关联相关议题，当拉取请求合并时会自动关闭对应议题
    body = f"resolve #{issue_number}"
    try:
        # 创建拉取请求
        pull = repo.create_pull(
            title=title,
            body=body,
            base=base,
            head=branch_name,
        )
        # 自动给拉取请求添加标签
        pull.add_to_labels(info.get_type().value)
    except:
        logging.info("该分支的拉取请求已创建，请前往查看")


def get_pull_requests_by_label(repo: "Repository", label: str) -> list["PullRequest"]:
    """获取所有带有指定标签的拉取请求"""
    pulls = list(repo.get_pulls(state="open"))
    return [pull for pull in pulls if label in [label.name for label in pull.labels]]


def extract_issue_number_from_ref(ref: str) -> Optional[int]:
    """从 Ref 中提取议题号"""
    match = re.search(rf"{BRANCH_NAME_PREFIX}(\d+)", ref)
    if match:
        return int(match.group(1))


def resolve_conflict_pull_requests(pulls: list["PullRequest"], repo: "Repository"):
    """根据关联的议题提交来解决冲突

    参考对应的议题重新更新对应分支
    """
    for pull in pulls:
        # 回到主分支
        run_shell_command(["git", "checkout", g.settings.input_config.base])
        # 切换到对应分支
        run_shell_command(["git", "switch", "-C", pull.head.ref])

        issue_number = extract_issue_number_from_ref(pull.head.ref)
        if not issue_number:
            logging.error(f"无法获取 {pull.title} 对应的议题")
            return

        logging.info(f"正在处理 {pull.title}")
        issue = repo.get_issue(issue_number)
        publish_type = get_type_by_labels(issue.labels)

        if publish_type:
            info = extract_publish_info_from_issue(issue, publish_type)
            if isinstance(info, PublishInfo):
                info.update_file()
                commit_and_push(info, pull.head.ref)
                logging.info("拉取请求更新完毕")
            else:
                logging.info("发布没通过检查，已跳过")


def extract_publish_info_from_issue(
    issue: "Issue", publish_type: PublishType
) -> Union[PublishInfo, MyValidationError]:
    """从议题中提取发布所需数据"""
    try:
        if publish_type == PublishType.BOT:
            return BotPublishInfo.from_issue(issue)
        elif publish_type == PublishType.PLUGIN:
            return PluginPublishInfo.from_issue(issue)
        return AdapterPublishInfo.from_issue(issue)
    except MyValidationError as e:
        return e


def comment_issue(issue: "Issue", body: str):
    """在议题中发布评论"""
    logging.info("开始发布评论")

    footer: str

    # 重复利用评论
    # 如果发现之前评论过，直接修改之前的评论
    comments = issue.get_comments()
    reusable_comment = next(
        filter(lambda x: PUBLISH_BOT_MARKER in x.body, comments), None
    )
    if reusable_comment:
        footer = f"{REUSE_MESSAGE}\n\n{POWERED_BY_BOT_MESSAGE}"
    else:
        footer = f"{POWERED_BY_BOT_MESSAGE}"

    # 添加发布机器人评论的标志
    footer += f"\n{PUBLISH_BOT_MARKER}"

    comment = COMMENT_MESSAGE_TEMPLATE.format(
        title=COMMENT_TITLE, body=body, footer=footer
    )
    if reusable_comment:
        logging.info(f"发现已有评论 {reusable_comment.id}，正在修改")
        reusable_comment.edit(comment)
        logging.info("评论修改完成")
    else:
        issue.create_comment(comment)
        logging.info("评论创建完成")
