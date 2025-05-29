from githubkit.rest import PullRequestSimple
from nonebot.adapters.github import GitHubBot
from nonebot.params import Depends

from src.plugins.github.depends import (
    get_issue_title,
    get_repo_info,
    get_type_by_labels_name,
)
from src.plugins.github.plugins.publish import utils
from src.providers.models import RepoInfo
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
