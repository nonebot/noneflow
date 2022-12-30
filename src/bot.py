import logging
from typing import TYPE_CHECKING

from githubkit import GitHub
from githubkit.webhooks import (
    IssueCommentCreated,
    IssuesEdited,
    IssuesOpened,
    IssuesReopened,
    PullRequestClosed,
    parse_without_name,
)

import src.globals as g

from .constants import (
    BRANCH_NAME_PREFIX,
    COMMENT_MESSAGE_TEMPLATE,
    COMMENT_TITLE,
    POWERED_BY_BOT_MESSAGE,
    PUBLISH_BOT_MARKER,
    REUSE_MESSAGE,
    SKIP_PLUGIN_TEST_COMMENT,
)
from .models import PublishInfo
from .utils import (
    commit_and_push,
    extract_issue_number_from_ref,
    extract_publish_info_from_issue,
    get_type_by_labels,
    get_type_by_title,
    run_shell_command,
)

if TYPE_CHECKING:
    from githubkit.rest.models import PullRequestSimple


class Bot:
    def __init__(self) -> None:
        self.github = GitHub(g.settings.input_token.get_secret_value())
        self.owner, self.name = g.settings.github_repository.split("/")

    def run(self):
        if not g.settings.github_event_path.is_file():
            logging.error(f"没有在 {g.settings.github_event_path} 找到 GitHub 事件文件")
            return

        event = parse_without_name(g.settings.github_event_path.read_text())

        if isinstance(event, PullRequestClosed):
            self.process_pull_request_event(event)
        elif isinstance(event, (IssuesOpened, IssuesReopened, IssuesEdited)):
            self.process_issues_event(event)
        elif isinstance(event, IssueCommentCreated):
            self.process_issue_comment_event(event)
        else:
            logging.info(f"不支持的事件: {event}，已跳过")

    def process_pull_request_event(self, event: PullRequestClosed):
        # 只处理支持标签的拉取请求
        publish_type = get_type_by_labels(event.pull_request.labels)
        if not publish_type:
            logging.info("拉取请求与发布无关，已跳过")
            return

        ref = event.pull_request.head.ref
        related_issue_number = extract_issue_number_from_ref(ref)
        if not related_issue_number:
            logging.error("无法获取相关的议题编号")
            return

        issue = self.github.rest.issues.get(
            self.owner, self.name, related_issue_number
        ).parsed_data
        if issue.state == "open":
            logging.info(f"正在关闭议题 #{related_issue_number}")
            self.github.rest.issues.update(
                self.owner,
                self.name,
                related_issue_number,
                state="closed",
                state_reason="completed"
                if event.pull_request.merged
                else "not_planned",
            )
        logging.info(f"议题 #{related_issue_number} 已关闭")

        try:
            run_shell_command(["git", "push", "origin", "--delete", ref])
            logging.info(f"已删除对应分支")
        except:
            logging.info("对应分支不存在或已删除")

        if event.pull_request.merged:
            logging.info("发布的拉取请求已合并，准备更新拉取请求的提交")
            pull_requests = self.get_pull_requests_by_label(publish_type.value)
            self.resolve_conflict_pull_requests(pull_requests)
        else:
            logging.info("发布的拉取请求未合并，已跳过")

    def process_issues_event(self, event: IssuesOpened | IssuesReopened | IssuesEdited):
        issue_number = event.issue.number
        self.process_publish_check(issue_number)

    def process_issue_comment_event(self, event: IssueCommentCreated):
        issue_number = event.issue.number
        self.process_publish_check(issue_number)

    def process_publish_check(self, issue_number: int):
        issue = self.github.rest.issues.get(
            self.owner, self.name, issue_number
        ).parsed_data

        if issue.pull_request:
            logging.info("评论在拉取请求下，已跳过")
            return

        if issue.state != "open":
            logging.info("议题未开启，已跳过")
            return

        publish_type = get_type_by_title(issue.title)
        if not publish_type:
            logging.info("议题与发布无关，已跳过")
            return

        # 自动给议题添加标签
        self.github.rest.issues.add_labels(
            self.owner, self.name, issue_number, labels=[publish_type.value]
        )

        # 是否需要跳过插件测试
        g.skip_plugin_test = self.should_skip_plugin_test(issue_number)

        # 检查是否满足发布要求
        # 仅在通过检查的情况下创建拉取请求
        info = extract_publish_info_from_issue(issue, publish_type)
        if isinstance(info, PublishInfo):
            # 拉取请求与议题的标题
            title = f"{info.get_type().value}: {info.name}"
            # 修改议题标题
            if issue.title != title:
                self.github.rest.issues.update(
                    self.owner, self.name, issue_number, title=title
                )
                logging.info(f"议题标题已修改为 {title}")
            # 创建新分支
            # 命名示例 publish/issue123
            branch_name = f"{BRANCH_NAME_PREFIX}{issue.number}"
            run_shell_command(["git", "switch", "-C", branch_name])
            # 更新文件并提交更改
            info.update_file()
            commit_and_push(info, branch_name, issue.number)
            # 创建拉取请求
            self.create_pull_request(info, branch_name, issue.number, title)
            message = info.validation_message
        else:
            message = info.message
            logging.info("发布没通过检查，暂不创建拉取请求")

        self.comment_issue(issue.number, message)

    def get_pull_requests_by_label(self, label: str) -> list["PullRequestSimple"]:
        """获取所有带有指定标签的拉取请求"""
        pulls = self.github.rest.pulls.list(
            self.owner, self.name, state="open"
        ).parsed_data
        return [
            pull for pull in pulls if label in [label.name for label in pull.labels]
        ]

    def resolve_conflict_pull_requests(self, pulls: list["PullRequestSimple"]):
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
            issue = self.github.rest.issues.get(
                self.owner, self.name, issue_number
            ).parsed_data

            publish_type = get_type_by_labels(issue.labels)
            if publish_type:
                info = extract_publish_info_from_issue(issue, publish_type)
                if isinstance(info, PublishInfo):
                    info.update_file()
                    commit_and_push(info, pull.head.ref, issue_number)
                    logging.info("拉取请求更新完毕")
                else:
                    logging.info("发布没通过检查，已跳过")

    def should_skip_plugin_test(self, issue_number: int) -> bool:
        """判断是否跳过插件测试"""
        comments = self.github.rest.issues.list_comments(
            self.owner, self.name, issue_number
        ).parsed_data
        for comment in comments:
            author_association = comment.author_association
            if comment.body == SKIP_PLUGIN_TEST_COMMENT and author_association in [
                "OWNER",
                "MEMBER",
            ]:
                return True
        return False

    def create_pull_request(
        self, info: PublishInfo, branch_name: str, issue_number: int, title: str
    ):
        """创建拉取请求

        同时添加对应标签
        内容关联上对应的议题
        """
        # 关联相关议题，当拉取请求合并时会自动关闭对应议题
        body = f"resolve #{issue_number}"
        # 创建拉取请求
        resp = self.github.rest.pulls.create(
            self.owner,
            self.name,
            title=title,
            body=body,
            base=g.settings.input_config.base,
            head=branch_name,
        )
        if resp.status_code == 200:
            pull = resp.parsed_data
            # 自动给拉取请求添加标签
            self.github.rest.issues.add_labels(
                self.owner, self.name, pull.number, labels=[info.get_type().value]
            )
        else:
            logging.info("该分支的拉取请求已创建，请前往查看")

            pull = self.github.rest.pulls.list(
                self.owner, self.name, head=f"{self.owner}:{branch_name}"
            ).parsed_data[0]
            if pull.title != title:
                self.github.rest.pulls.update(
                    self.owner, self.name, pull.number, title=title
                )
                logging.info(f"拉取请求标题已修改为 {title}")

    def comment_issue(self, issue_number: int, body: str):
        """在议题中发布评论"""
        logging.info("开始发布评论")

        footer: str

        # 重复利用评论
        # 如果发现之前评论过，直接修改之前的评论
        comments = self.github.rest.issues.list_comments(
            self.owner, self.name, issue_number
        ).parsed_data
        reusable_comment = next(
            filter(
                lambda x: PUBLISH_BOT_MARKER in (x.body if x.body else ""), comments
            ),
            None,
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
            if reusable_comment.body != comment:
                self.github.rest.issues.update_comment(
                    self.owner, self.name, reusable_comment.id, body=comment
                )
                logging.info("评论修改完成")
            else:
                logging.info("评论内容无变化，跳过修改")
        else:
            self.github.rest.issues.create_comment(
                self.owner, self.name, issue_number, body=comment
            )
            logging.info("评论创建完成")
