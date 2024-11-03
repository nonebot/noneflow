from typing import Literal

from githubkit.rest import PullRequestSimple
from githubkit.typing import Missing
from githubkit.utils import UNSET
from nonebot import logger
from nonebot.adapters.github import Bot
from pydantic import ConfigDict

from src.plugins.github.constants import NONEFLOW_MARKER
from src.plugins.github.models import GitHandler, RepoInfo


class GithubHandler(GitHandler):
    """Bot 相关的 Github 操作"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    bot: Bot
    repo_info: RepoInfo

    async def update_issue_title(self, title: str, issue_number: int):
        """修改议题标题"""
        await self.bot.rest.issues.async_update(
            **self.repo_info.model_dump(), issue_number=issue_number, title=title
        )
        logger.info(f"标题已修改为 {title}")

    async def update_issue_content(self, body: str, issue_number: int):
        """更新议题内容"""
        await self.bot.rest.issues.async_update(
            **self.repo_info.model_dump(), issue_number=issue_number, body=body
        )
        logger.info("议题内容已修改")

    async def create_dispatch_event(
        self, event_type: str, client_payload: dict, repo: RepoInfo | None = None
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
        """拉取所有评论"""
        return (
            await self.bot.rest.issues.async_list_comments(
                **self.repo_info.model_dump(), issue_number=issue_number
            )
        ).parsed_data

    async def create_comment(self, comment: str, issue_number: int):
        """发布评论"""
        await self.bot.rest.issues.async_create_comment(
            **self.repo_info.model_dump(), issue_number=issue_number, body=comment
        )

    async def update_comment(self, comment_id: int, comment: str):
        """修改评论"""
        await self.bot.rest.issues.async_update_comment(
            **self.repo_info.model_dump(), comment_id=comment_id, body=comment
        )

    async def comment_issue(self, comment: str, issue_number: int):
        """发布评论，若之前已评论过，则会进行复用"""
        logger.info("开始发布评论")

        # 重复利用评论
        # 如果发现之前评论过，直接修改之前的评论
        comments = await self.list_comments(issue_number=issue_number)
        reusable_comment = next(
            filter(lambda x: NONEFLOW_MARKER in (x.body if x.body else ""), comments),
            None,
        )

        if reusable_comment:
            logger.info(f"发现已有评论 {reusable_comment.id}，正在修改")
            if reusable_comment.body != comment:
                await self.update_comment(reusable_comment.id, comment)
                logger.info("评论修改完成")
            else:
                logger.info("评论内容无变化，跳过修改")
        else:
            await self.create_comment(comment, issue_number)
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

    async def get_pull_request(self, pull_number: int):
        """获取拉取请求"""
        return (
            await self.bot.rest.pulls.async_get(
                **self.repo_info.model_dump(), pull_number=pull_number
            )
        ).parsed_data

    async def draft_pull_request(self, branch_name: str):
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
            logger.info("没通过检查，已将之前的拉取请求转换为草稿")

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

    async def get_pull_request_by_branch(self, branch_name: str) -> PullRequestSimple:
        """根据分支的名称获取对应的拉取请求示例"""
        return (
            await self.bot.rest.pulls.async_list(
                **self.repo_info.model_dump(),
                head=f"{self.repo_info.owner}:{branch_name}",
            )
        ).parsed_data[0]

    async def update_pull_request_status(self, title: str, branch_name: str):
        """拉取请求若为草稿状态则标记为可评审，若标题不符则修改标题"""
        pull = await self.get_pull_request_by_branch(branch_name)
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

    async def create_pull_request(
        self,
        base_branch: str,
        title: str,
        branch_name: str,
        label: str | list[str],
        body: str | None,
    ) -> int:
        """创建拉取请求并分配标签，若存在请求会导致 raise RequestFailed"""
        if body is None:
            body = ""

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
        return pull.number

    async def ready_pull_request(self, node_id: int):
        """将拉取请求标记为可评审"""
        await self.bot.async_graphql(
            query="""mutation markPullRequestReadyForReview($pullRequestId: ID!) {
                        markPullRequestReadyForReview(input: {pullRequestId: $pullRequestId}) {
                            clientMutationId
                        }
                    }""",
            variables={"pullRequestId": node_id},
        )
        logger.info("拉取请求已标记为可评审")

    async def update_pull_request_title(self, title: str, branch_name: int):
        """修改拉取请求标题"""
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

    async def get_user_name(self, account_id: int):
        """根据用户 ID 获取用户名"""
        return (
            await self.bot.rest.users.async_get_by_id(account_id=account_id)
        ).parsed_data.login

    async def get_user_id(self, account_name: str):
        """根据用户名获取用户 ID"""
        return (
            await self.bot.rest.users.async_get_by_username(username=account_name)
        ).parsed_data.id

    async def get_issue(self, issue_number: int):
        """获取议题"""
        return (
            await self.bot.rest.issues.async_get(
                **self.repo_info.model_dump(), issue_number=issue_number
            )
        ).parsed_data

    async def to_issue_handler(self, issue_number: int):
        """获取议题处理器"""
        from src.plugins.github.models.issue import IssueHandler

        issue = await self.get_issue(issue_number)

        return IssueHandler(bot=self.bot, repo_info=self.repo_info, issue=issue)
