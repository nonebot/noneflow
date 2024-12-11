from githubkit.exception import RequestFailed
from nonebot import logger
from pydantic_core import PydanticCustomError

from src.plugins.github import plugin_config
from src.plugins.github.constants import REMOVE_LABEL
from src.plugins.github.depends.utils import (
    extract_issue_number_from_ref,
    get_type_by_labels,
)
from src.plugins.github.handlers import GithubHandler, IssueHandler
from src.plugins.github.typing import PullRequestList
from src.plugins.github.utils import commit_message
from src.providers.utils import dump_json5
from src.providers.validation.models import PublishType

from .constants import COMMIT_MESSAGE_PREFIX
from .validation import RemoveInfo, load_publish_data, validate_author_info


def update_file(result: RemoveInfo):
    """删除对应的包储存在 registry 里的数据"""
    logger.info("开始更新文件")

    match result.publish_type:
        case PublishType.PLUGIN:
            path = plugin_config.input_config.plugin_path
        case PublishType.BOT:
            path = plugin_config.input_config.bot_path
        case PublishType.ADAPTER:
            path = plugin_config.input_config.adapter_path
        case _:
            raise ValueError("不支持的删除类型")

    data = load_publish_data(result.publish_type)
    # 删除对应的数据项
    data.pop(result.key)
    dump_json5(path, list(data.values()))
    logger.info(f"已更新 {path.name} 文件")


async def process_pull_reqeusts(
    handler: IssueHandler,
    store_handler: GithubHandler,
    result: RemoveInfo,
    branch_name: str,
    title: str,
):
    """
    根据发布信息合法性创建拉取请求
    """
    message = commit_message(COMMIT_MESSAGE_PREFIX, result.name, handler.issue_number)

    # 切换分支
    handler.switch_branch(branch_name)
    # 更新文件并提交更改
    update_file(result)
    store_handler.commit_and_push(message, branch_name, author=handler.author)
    # 创建拉取请求
    logger.info("开始创建拉取请求")

    try:
        pull_number = await store_handler.create_pull_request(
            plugin_config.input_config.base,
            title,
            branch_name,
            body=f"resolve {handler.repo_info}#{handler.issue_number}",
        )
        await store_handler.add_labels(
            pull_number, [REMOVE_LABEL, result.publish_type.value]
        )
    except RequestFailed:
        # 如果之前已经创建了拉取请求，则将其转换为草稿
        logger.info("该分支的拉取请求已创建，请前往查看")
        await store_handler.update_pull_request_status(title, branch_name)


async def resolve_conflict_pull_requests(
    handler: GithubHandler, pulls: PullRequestList
):
    """根据关联的议题提交来解决冲突

    直接重新提交之前分支中的内容
    """

    for pull in pulls:
        issue_number = extract_issue_number_from_ref(pull.head.ref)
        if not issue_number:
            logger.error(f"无法获取 {pull.title} 对应的议题编号")
            continue

        logger.info(f"正在处理 {pull.title}")
        if pull.draft:
            logger.info("拉取请求为草稿，跳过处理")
            continue

        # 根据标签获取发布类型
        publish_type = get_type_by_labels(pull.labels)
        issue_handler = await handler.to_issue_handler(issue_number)

        if publish_type:
            # 验证作者信息
            try:
                result = await validate_author_info(issue_handler.issue, publish_type)
            except PydanticCustomError as e:
                logger.error(f"验证作者信息失败: {e}")
                continue

            # 每次切换前都要确保回到主分支
            handler.checkout_branch(plugin_config.input_config.base)
            # 切换到对应分支
            handler.switch_branch(pull.head.ref)
            # 更新文件
            update_file(result)

            # 生成提交信息并推送
            message = commit_message(COMMIT_MESSAGE_PREFIX, result.name, issue_number)
            issue_handler.commit_and_push(message, pull.head.ref)

            logger.info("拉取请求更新完毕")
