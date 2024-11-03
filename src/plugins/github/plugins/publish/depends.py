from githubkit.rest import PullRequestSimple
from nonebot.adapters.github import GitHubBot
from nonebot.params import Depends

from src.plugins.github.depends import (
    get_installation_id,
    get_issue_number,
    get_issue_title,
    get_repo_info,
    get_type_by_labels_name,
)
from src.plugins.github.models import IssueHandler, RepoInfo
from src.plugins.github.plugins.publish import utils
from src.providers.validation.models import PublishType


def get_type_by_title(title: str = Depends(get_issue_title)) -> PublishType | None:
    """通过标题获取类型"""
    return utils.get_type_by_title(title)


async def get_pull_requests_by_label(
    bot: GitHubBot,
    repo_info: RepoInfo = Depends(get_repo_info),
    publish_type: PublishType = Depends(get_type_by_labels_name),
) -> list[PullRequestSimple]:
    pulls = (
        await bot.rest.pulls.async_list(**repo_info.model_dump(), state="open")
    ).parsed_data
    return [
        pull
        for pull in pulls
        if publish_type.value in [label.name for label in pull.labels]
    ]


async def get_issue_handler(
    bot: GitHubBot,
    installation_id: int = Depends(get_installation_id),
    repo_info: RepoInfo = Depends(get_repo_info),
    issue_number: int = Depends(get_issue_number),
):
    async with bot.as_installation(installation_id):
        # 因为 Actions 会排队，触发事件相关的议题在 Actions 执行时可能已经被关闭
        # 所以需要获取最新的议题状态
        issue = (
            await bot.rest.issues.async_get(
                **repo_info.model_dump(), issue_number=issue_number
            )
        ).parsed_data

        return IssueHandler(bot=bot, repo_info=repo_info, issue=issue)
