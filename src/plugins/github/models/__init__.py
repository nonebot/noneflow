from typing import Literal
from githubkit.rest import Issue, PullRequestSimple
from nonebot import logger
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from nonebot.adapters.github import Bot

from githubkit.exception import RequestFailed
from githubkit.utils import UNSET
from githubkit.typing import Missing

from src.plugins.github.constants import NONEFLOW_MARKER
from src.plugins.github.utils import run_shell_command


class RepoInfo(BaseModel):
    """仓库信息"""

    owner: str
    repo: str


class GitHandler(BaseModel):
    """Git 操作"""

    def commit_and_push(self, message: str, branch_name: str, author: str):
        run_shell_command(["git", "config", "--global", "user.name", author])
        user_email = f"{author}@users.noreply.github.com"
        run_shell_command(["git", "config", "--global", "user.email", user_email])
        run_shell_command(["git", "add", "-A"])
        try:
            run_shell_command(["git", "commit", "-m", message])
        except Exception:
            # 如果提交失败，因为是 pre-commit hooks 格式化代码导致的，所以需要再次提交
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

    def delete_origin_branch(self, branch_name: str):
        """删除远程分支"""
        run_shell_command(["git", "push", "origin", "--delete", branch_name])


class GithubHandler(GitHandler):
    """Bot 相关的 Github 操作"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    bot: Bot
    repo_info: RepoInfo

    async def create_dispatch_event(
        self, repo: RepoInfo | None, event_type: str, client_payload: dict
    ):
        if repo is None:
            repo = self.repo_info
        await self.bot.rest.repos.async_create_dispatch_event(
            repo=repo.repo,
            owner=repo.owner,
            event_type=event_type,
            client_payload=client_payload,  # type: ignore
        )

    async def list_comments(self, issue_number: int):
        return (
            await self.bot.rest.issues.async_list_comments(
                **self.repo_info.model_dump(), issue_number=issue_number
            )
        ).parsed_data

    async def comment_issue(self, comment: str, issue_number: int):
        """发布评论
        若之前发布过评论，则修改之前的评论
        """
        logger.info("开始发布评论")

        # 重复利用评论
        # 如果发现之前评论过，直接修改之前的评论
        comments = (
            await self.bot.rest.issues.async_list_comments(
                **self.repo_info.model_dump(), issue_number=issue_number
            )
        ).parsed_data
        reusable_comment = next(
            filter(lambda x: NONEFLOW_MARKER in (x.body if x.body else ""), comments),
            None,
        )

        # comment = await render_comment(result, bool(reusable_comment))
        if reusable_comment:
            logger.info(f"发现已有评论 {reusable_comment.id}，正在修改")
            if reusable_comment.body != comment:
                await self.bot.rest.issues.async_update_comment(
                    **self.repo_info.model_dump(),
                    comment_id=reusable_comment.id,
                    body=comment,
                )
                logger.info("评论修改完成")
            else:
                logger.info("评论内容无变化，跳过修改")
        else:
            await self.bot.rest.issues.async_create_comment(
                **self.repo_info.model_dump(),
                issue_number=issue_number,
                body=comment,
            )
            logger.info("评论创建完成")

    async def get_pull_requests_by_label(self, label: str) -> list[PullRequestSimple]:
        """根据标签获取拉取请求"""
        pulls = (
            await self.bot.rest.pulls.async_list(
                **self.repo_info.model_dump(), state="open"
            )
        ).parsed_data
        return [
            pull for pull in pulls if label in [label.name for label in pull.labels]
        ]

    async def pull_request_to_draft(self, branch_name: str):
        """
        将拉取请求转换为草稿
        """
        pulls = (
            await self.bot.rest.pulls.async_list(
                **self.repo_info.model_dump(),
                head=f"{self.repo_info.owner}:{branch_name}",
            )
        ).parsed_data
        if pulls and (pull := pulls[0]) and not pull.draft:
            await self.bot.async_graphql(
                query="""mutation convertPullRequestToDraft($pullRequestId: ID!) {
                    convertPullRequestToDraft(input: {pullRequestId: $pullRequestId}) {
                        clientMutationId
                    }
                }""",
                variables={"pullRequestId": pull.node_id},
            )
            logger.info("删除没通过检查，已将之前的拉取请求转换为草稿")
        else:
            logger.info("没通过检查，暂不创建拉取请求")

    async def merge_pull_request(
        self,
        pull_number: int,
        merge_method: Missing[Literal["merge", "squash", "rebase"]] = UNSET,
    ):
        """合并拉取请求"""
        await self.bot.rest.pulls.async_merge(
            **self.repo_info.model_dump(),
            pull_number=pull_number,
            merge_method=merge_method,
        )
        logger.info(f"拉取请求 #{pull_number} 已合并")

    async def create_pull_request(
        self,
        base_branch: str,
        title: str,
        branch_name: str,
        label: str | list[str],
        issue_number: int,
    ):
        """创建拉取请求"""
        body = f"resolve #{issue_number}"

        try:
            # 创建拉取请求
            resp = await self.bot.rest.pulls.async_create(
                **self.repo_info.model_dump(),
                title=title,
                body=body,
                base=base_branch,
                head=branch_name,
            )
            pull = resp.parsed_data

            # 自动给拉取请求添加标签
            await self.bot.rest.issues.async_add_labels(
                **self.repo_info.model_dump(),
                issue_number=pull.number,
                labels=[label] if isinstance(label, str) else label,
            )
            logger.info("拉取请求创建完毕")
        except RequestFailed:
            logger.info("该分支的拉取请求已创建，请前往查看")

            pull = (
                await self.bot.rest.pulls.async_list(
                    **self.repo_info.model_dump(),
                    head=f"{self.repo_info.owner}:{branch_name}",
                )
            ).parsed_data[0]
            if pull.title != title:
                await self.bot.rest.pulls.async_update(
                    **self.repo_info.model_dump(), pull_number=pull.number, title=title
                )
                logger.info(f"拉取请求标题已修改为 {title}")
            if pull.draft:
                await self.bot.async_graphql(
                    query="""mutation markPullRequestReadyForReview($pullRequestId: ID!) {
                        markPullRequestReadyForReview(input: {pullRequestId: $pullRequestId}) {
                            clientMutationId
                        }
                    }""",
                    variables={"pullRequestId": pull.node_id},
                )
                logger.info("拉取请求已标记为可评审")


class IssueHandler(GithubHandler):
    """Issue 的相关 Github/Git 操作"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    issue: Issue
    issue_number: int
    author_id: int = 0
    author: str = ""

    @model_validator(mode="before")
    @classmethod
    def issuehandler_validator(cls, data):
        if data.get("author_id") is None and data.get("issue"):
            issue = data["issue"]
            data["author_id"] = issue.user.id if issue.user else 0
        if data.get("author") is None and data.get("issue"):
            issue = data["issue"]
            data["author"] = issue.user.login if issue.user else ""
        if data.get("issue_number") is None and data.get("issue"):
            issue = data["issue"]
            data["issue_number"] = issue.number
        return data

    async def update_issue_title(
        self,
        title: str,
    ):
        if self.issue and self.issue.title != title:
            await self.bot.rest.issues.async_update(
                **self.repo_info.model_dump(),
                issue_number=self.issue_number,
                title=title,
            )
            logger.info(f"标题已修改为 {title}")

    async def update_issue_content(self, body: str):
        """编辑议题内容"""
        await self.bot.rest.issues.async_update(
            **self.repo_info.model_dump(),
            issue_number=self.issue_number,
            body=body,
        )
        logger.info("议题内容已修改")

    async def close_issue(self, reason: str):
        """关闭议题"""
        if self.issue and self.issue.state == "open":
            logger.info(f"正在关闭议题 #{self.issue_number}")
            await self.bot.rest.issues.async_update(
                **self.repo_info.model_dump(),
                issue_number=self.issue_number,
                state="closed",
                state_reason=reason,
            )

    async def comment_issue(self, comment: str):
        return await super().comment_issue(comment, self.issue_number)

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

    async def list_comments(self):
        return await super().list_comments(self.issue_number)

    def commit_and_push(self, message: str, branch_name: str):
        return super().commit_and_push(message, branch_name, self.author)
