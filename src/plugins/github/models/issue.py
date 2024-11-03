from typing import Literal

from githubkit.rest import Issue
from nonebot import logger
from pydantic import ConfigDict

from src.plugins.github.constants import SKIP_COMMENT
from src.plugins.github.models import AuthorInfo, GithubHandler


class IssueHandler(GithubHandler):
    """Issue 的相关 Github/Git 操作"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    issue: Issue

    @property
    def issue_number(self) -> int:
        return self.issue.number

    @property
    def author_info(self) -> AuthorInfo:
        return AuthorInfo.from_issue(self.issue)

    @property
    def author(self) -> str:
        return self.author_info.author

    @property
    def author_id(self) -> int:
        return self.author_info.author_id

    async def update_issue_title(self, title: str, issue_number: int | None = None):
        """修改议题标题"""
        if issue_number is None:
            issue_number = self.issue_number

        # 只有修改的议题标题和原标题不一致时才会进行修改
        # 并且需要是同一个议题
        if self.issue_number == issue_number and self.issue.title == title:
            return

        await super().update_issue_title(title, issue_number)

        # 更新缓存属性，避免重复或错误操作
        self.issue.title = title

    async def update_issue_content(self, body: str, issue_number: int | None = None):
        """更新议题内容"""
        if issue_number is None:
            issue_number = self.issue_number

        await super().update_issue_content(body, issue_number)

        # 更新缓存属性，避免重复或错误操作
        self.issue.body = body

    async def close_issue(
        self, reason: Literal["completed", "not_planned", "reopened"]
    ):
        """关闭议题"""
        if self.issue and self.issue.state == "open":
            logger.info(f"正在关闭议题 #{self.issue_number}")
            await self.bot.rest.issues.async_update(
                **self.repo_info.model_dump(),
                issue_number=self.issue_number,
                state="closed",
                state_reason=reason,
            )

    async def create_pull_request(
        self,
        base_branch: str,
        title: str,
        branch_name: str,
        label: str | list[str],
        body: str | None = None,
    ):
        if body is None:
            body = f"resolve #{self.issue_number}"

        return await super().create_pull_request(
            base_branch, title, branch_name, label, body
        )

    async def should_skip_test(self) -> bool:
        """判断评论是否包含跳过的标记"""
        comments = await self.list_comments(self.issue_number)
        for comment in comments:
            author_association = comment.author_association
            if comment.body == SKIP_COMMENT and author_association in [
                "OWNER",
                "MEMBER",
            ]:
                return True
        return False

    async def list_comments(self, issue_number: int | None = None):
        """拉取所有评论"""
        if issue_number is None:
            issue_number = self.issue_number

        return await super().list_comments(issue_number)

    async def comment_issue(self, comment: str, issue_number: int | None = None):
        """发布评论，若之前已评论过，则会进行复用"""
        if issue_number is None:
            issue_number = self.issue_number

        await super().comment_issue(comment, issue_number)

    def commit_and_push(
        self,
        message: str,
        branch_name: str,
        author: str | None = None,
    ):
        if author is None:
            author = self.author
        return super().commit_and_push(message, branch_name, author)
