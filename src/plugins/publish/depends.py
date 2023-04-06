from githubkit.rest.models import IssuePropLabelsItemsOneof1, Label, PullRequestSimple
from githubkit.webhooks.models import Label as WebhookLabel
from nonebot import logger
from nonebot.adapters.github import GitHubBot, PullRequestClosed
from nonebot.params import Depends

from .models import PublishType, RepoInfo


def get_repo_info(event: PullRequestClosed) -> RepoInfo:
    """获取仓库信息"""
    repo = event.payload.repository
    return RepoInfo(owner=repo.owner.login, name=repo.name)


def get_labels(event: PullRequestClosed) -> list["WebhookLabel"]:
    """获取标签"""
    labels = event.payload.pull_request.labels
    return labels


def get_type_by_labels(
    labels: list[Label]
    | list[WebhookLabel]
    | list[str | IssuePropLabelsItemsOneof1] = Depends(get_labels),
) -> PublishType | None:
    """通过标签获取类型"""
    for label in labels:
        if isinstance(label, str):
            continue
        if label.name == PublishType.BOT.value:
            return PublishType.BOT
        if label.name == PublishType.PLUGIN.value:
            return PublishType.PLUGIN
        if label.name == PublishType.ADAPTER.value:
            return PublishType.ADAPTER
    logger.info("议题与发布无关")


def get_pull_requests_by_label(
    bot: GitHubBot,
    repo_info: RepoInfo = Depends(get_repo_info),
    publish_type: PublishType = Depends(get_type_by_labels),
) -> list[PullRequestSimple]:
    pulls = bot.rest.pulls.list(**repo_info.dict(), state="open").parsed_data
    return [
        pull
        for pull in pulls
        if publish_type.value in [label.name for label in pull.labels]
    ]
