from typing import Any, Literal
from githubkit.rest import Issue
from nonebot import logger
from pydantic import (
    ConfigDict,
    model_validator,
)

from src.plugins.github.models import AuthorInfo, GithubHandler
from src.plugins.github.constants import SKIP_COMMENT


class IssueHandler(GithubHandler):
    """Issue 的相关 Github/Git 操作"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    issue: Issue
    issue_number: int
    author_id: int = 0
    author: str = ""

    @model_validator(mode="before")
    @classmethod
    def issue_handler_validator(cls, data: dict[str, Any]):
        issue = data.get("issue")
        if data.get("issue_number") is None and issue:
            data["issue_number"] = issue.number
        if issue:
            data.update(AuthorInfo.from_issue(issue).model_dump())
        return data

    async def update_issue_title(
        self,
        title: str,
    ):
        """修改议题标题"""
        if self.issue and self.issue.title != title:
            await super().update_issue_title(self.issue_number, title)
            logger.info(f"标题已修改为 {title}")

    async def update_issue_content(self, body: str):
        """编辑议题内容"""
        await super().update_issue_content(self.issue_number, body)

        # 更新缓存属性，避免重复或错误操作
        self.issue.body = body

        logger.info("议题内容已修改")

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
    ):
        return await super().create_pull_request(
            base_branch, title, branch_name, label, self.issue_number
        )

    async def comment_issue(self, comment: str):
        return await super().comment_issue(comment, self.issue_number)

    async def should_skip_plugin_test(self) -> bool:
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

    def commit_and_push(self, message: str, branch_name: str):
        return super().commit_and_push(message, branch_name, self.author)
