import logging

from github.Repository import Repository

from .models import (
    PartialGitHubIssuesEvent,
    PartialGitHubPullRequestEvent,
    PartialGitHubPushEvent,
    Settings,
)
from .utils import (
    comment_issue,
    commit_and_push,
    create_pull_request,
    extract_issue_number_from_ref,
    extract_publish_info_from_issue,
    get_pull_requests_by_label,
    get_type_by_commit_message,
    get_type_by_labels,
    get_type_by_title,
    resolve_conflict_pull_requests,
    run_shell_command,
)


def process_pull_request_event(settings: Settings, repo: Repository):
    """处理 Pull Request 事件"""
    event = PartialGitHubPullRequestEvent.parse_file(settings.github_event_path)

    # 因为合并拉取请求只会触发 closed 事件
    # 其他事件均对商店发布流程无影响
    if event.action != "closed":
        logging.info("事件不是关闭拉取请求，已跳过")
        return
    pull_request = repo.get_pull(event.pull_request.number)

    # 只处理支持标签的拉取请求
    publish_type = get_type_by_labels(pull_request.labels)
    if not publish_type:
        logging.info("拉取请求与发布无关，已跳过")
        return

    ref = pull_request.head.ref
    related_issue_number = extract_issue_number_from_ref(ref)
    if not related_issue_number:
        logging.error("无法获取相关的议题编号")
        return

    issue = repo.get_issue(related_issue_number)
    issue.edit(state="closed")
    logging.info(f"议题 #{related_issue_number} 已关闭")

    try:
        run_shell_command(f"git push origin --delete {ref}")
        logging.info(f"已删除对应分支")
    except:
        logging.info("对应分支不存在或已删除")

    if pull_request.merged:
        logging.info("发布的拉取请求已合并，准备更新拉取请求的提交")
        pull_requests = get_pull_requests_by_label(repo, publish_type.value)
        resolve_conflict_pull_requests(settings, pull_requests, repo)
    else:
        logging.info("发布的拉取请求未合并，已跳过")


def process_push_event(settings: Settings, repo: Repository):
    """处理提交"""
    event = PartialGitHubPushEvent.parse_file(settings.github_event_path)

    publish_type = get_type_by_commit_message(event.head_commit.message)
    if not publish_type:
        logging.info("该提交不是发布，已跳过")
        return

    logging.info("发现提交为发布，准备更新拉取请求的提交")
    pull_requests = get_pull_requests_by_label(repo, publish_type.value)
    resolve_conflict_pull_requests(settings, pull_requests, repo)


def process_issues_event(settings: Settings, repo: Repository):
    """处理议题"""
    event = PartialGitHubIssuesEvent.parse_file(settings.github_event_path)
    if not event.action in ["opened", "reopened", "edited"]:
        logging.info("不支持的事件，已跳过")
        return
    issue = repo.get_issue(event.issue.number)

    publish_type = get_type_by_title(issue.title)

    if not publish_type:
        logging.info("")
        return

    info = extract_publish_info_from_issue(issue, publish_type)

    # 自动给议题添加标签
    issue.edit(labels=[publish_type.value])

    # 检查是否满足发布要求
    # 仅在通过检查的情况下创建拉取请求
    if info.is_valid():
        # 创建新分支
        # 命名示例 publish/issue123
        branch_name = f"publish/issue${issue.number}"
        run_shell_command(f"git checkout -b {branch_name}")
        # 更新文件并提交更改
        info.update_file(settings)
        commit_and_push(info, branch_name)
        # 创建拉取请求
        create_pull_request(
            repo, info, settings.input_config.base, branch_name, issue.number
        )

    comment_issue(issue, info.validate_message())
