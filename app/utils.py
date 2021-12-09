import logging
import re
import subprocess
from typing import Optional

from github.Issue import Issue
from github.Label import Label
from github.PullRequest import PullRequest
from github.Repository import Repository

from .models import AdapterInfo, BotInfo, PluginInfo, PublishInfo, PublishType, Settings


def run_shell_command(command: str):
    """运行 shell 命令

    如果遇到错误则抛出异常
    """
    subprocess.run(command, shell=True, check=True)


def get_type_by_labels(labels: list[Label]) -> Optional[PublishType]:
    """通过标签获取类型"""
    for label in labels:
        if label.name == "bot":
            return PublishType.BOT
        if label.name == "plugin":
            return PublishType.PLUGIN
        if label.name == "adapter":
            return PublishType.ADAPTER


def get_type_by_title(title: str) -> Optional[PublishType]:
    """通过标题获取类型"""
    if title.startswith("Bot:"):
        return PublishType.BOT
    if title.startswith("Plugin:"):
        return PublishType.PLUGIN
    if title.startswith("Adapter:"):
        return PublishType.ADAPTER


def get_type_by_commit_message(message: str) -> Optional[PublishType]:
    """通过提交信息获取类型"""
    if message.startswith(":beers: publish bot"):
        return PublishType.BOT
    if message.startswith(":beers: publish plugin"):
        return PublishType.PLUGIN
    if message.startswith(":beers: publish adapter"):
        return PublishType.ADAPTER


def commit_and_push(info: PublishInfo, branch_name: str):
    """提交并推送"""
    commit_message = f":beers: publish {info.get_type().value} {info.name}"
    run_shell_command(f"git config --global user.name {info.author}")
    user_email = f"{info.author}@users.noreply.github.com"
    run_shell_command(f"git config --global user.email {user_email}")
    run_shell_command(f"git add -A")
    run_shell_command(f"git commit -m {commit_message}")
    run_shell_command(f"git push origin {branch_name} -f")


# /**创建拉取请求
#  *
#  * 同时添加对应标签
#  * 内容关联上对应的议题
#  */
# export async function createPullRequest(
#   octokit: OctokitType,
#   info: Info,
#   issueNumber: number,
#   branchName: string,
#   base: string
# ): Promise<void> {
#   const pullRequestTitle = `${info.type}: ${info.name}`
#   // 关联相关议题，当拉取请求合并时会自动关闭对应议题
#   const pullRequestbody = `resolve #${issueNumber}`
#   try {
#     // 创建拉取请求
#     const pr = await octokit.pulls.create({
#       ...github.context.repo,
#       title: pullRequestTitle,
#       head: branchName,
#       base,
#       body: pullRequestbody
#     })
#     // 自动给拉取请求添加标签
#     await octokit.issues.addLabels({
#       ...github.context.repo,
#       issue_number: pr.data.number,
#       labels: [info.type]
#     })
#   } catch (error) {
#     if (error.message.includes(`A pull request already exists for`)) {
#       core.info('该分支的拉取请求已创建，请前往查看')
#     } else {
#       throw error
#     }
#   }
# }


def get_pull_requests_by_label(repo: Repository, label: str) -> list[PullRequest]:
    """获取所有带有指定标签的拉取请求"""
    pulls = list(repo.get_pulls(state="open"))
    return [pull for pull in pulls if label in [label.name for label in pull.labels]]


def extract_issue_number_from_ref(ref: str) -> Optional[int]:
    """从 Ref 中提取议题号"""
    match = re.match(r"\/issue(\d+)", ref)
    if match:
        return int(match.group(1))


def resolve_conflict_pull_requests(
    settings: Settings, pulls: list[PullRequest], repo: Repository
):
    """根据关联的议题提交来解决冲突

    参考对应的议题重新更新对应分支
    """
    for pull in pulls:
        # 切换到对应分支
        run_shell_command(f"git checkout -b {pull.head.ref}")
        # 重置之前的提交
        run_shell_command(f"git reset --hard {settings.input_config.base}")
        issue_number = extract_issue_number_from_ref(pull.head.ref)
        if not issue_number:
            logging.error(f"无法获取 {pull.title} 对应的议题")
            return

        logging.info(f"正在处理 {pull.title}")
        issue = repo.get_issue(issue_number)
        publish_type = get_type_by_labels(issue.labels)

        if publish_type:
            info = extract_publish_info_from_issue(issue, publish_type)
            info.update_file(settings)
            commit_and_push(info, pull.head.ref)
            logging.info("拉取请求更新完毕")


def extract_publish_info_from_issue(
    issue: Issue, publish_type: PublishType
) -> PublishInfo:
    """从议题中提取发布所需数据"""
    if publish_type == PublishType.BOT:
        return BotInfo.from_issue(issue)
    elif publish_type == PublishType.PLUGIN:
        return PluginInfo.from_issue(issue)
    return AdapterInfo.from_issue(issue)


# /**发布评论  */
# export async function publishComment(
#   octokit: OctokitType,
#   issue_number: number,
#   body: string
# ): Promise<void> {
#   // 给评论添加统一的标题
#   body = `${commentTitle}\n${body}`
#   core.info('开始发布评论')
#   if (!(await reuseComment(octokit, issue_number, body))) {
#     body += `\n\n---\n${poweredByBotMessage}`
#     await octokit.issues.createComment({
#       ...github.context.repo,
#       issue_number,
#       body
#     })
#     core.info('评论创建完成')
#   }
# }
# /**重复利用评论
#  *
#  * 如果发现之前评论过，直接修改之前的评论
#  */
# async function reuseComment(
#   octokit: OctokitType,
#   issue_number: number,
#   body: string
# ): Promise<boolean> {
#   const comments = await octokit.issues.listComments({
#     ...github.context.repo,
#     issue_number
#   })
#   if (comments) {
#     // 检查相关评论是否拥有统一的标题
#     const relatedComments = comments.data.filter(comment =>
#       comment.body?.startsWith(commentTitle)
#     )
#     if (!relatedComments) {
#       return false
#     }
#     const last_comment = relatedComments.pop()
#     const comment_id = last_comment?.id
#     if (comment_id) {
#       core.info(`发现已有评论 ${last_comment?.id}，正在修改`)
#       body += `\n\n---\n${reuseMessage}\n\n${poweredByBotMessage}`
#       octokit.issues.updateComment({
#         ...github.context.repo,
#         comment_id,
#         body
#       })
#       return true
#     }
#   }
#   return false
# }
