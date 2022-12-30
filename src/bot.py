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

if TYPE_CHECKING:
    from .models import Settings


class Bot:
    def __init__(self, settings: "Settings") -> None:
        self.settings = settings
        self.skip_plugin_test = False

        self.github = GitHub(self.settings.input_token.get_secret_value())
        self.repo_owner, self.repo_name = self.settings.github_repository.split("/")

    def run(self):
        if not self.settings.github_event_path.is_file():
            logging.error(f"没有在 {self.settings.github_event_path} 找到 GitHub 事件文件")
            return

        event = parse_without_name(self.settings.github_event_path.read_text())

        if isinstance(event, PullRequestClosed):
            self.process_pull_request_event(event)
        elif isinstance(event, (IssuesOpened, IssuesReopened, IssuesEdited)):
            self.process_issues_event(event)
        elif isinstance(event, IssueCommentCreated):
            self.process_issue_comment_event(event)
        else:
            logging.info(f"不支持的事件: {self.settings.github_event_name}，已跳过")

    def process_pull_request_event(self, event: PullRequestClosed):
        pass

    def process_issues_event(self, event: IssuesOpened | IssuesReopened | IssuesEdited):
        pass

    def process_issue_comment_event(self, event: IssueCommentCreated):
        pass
