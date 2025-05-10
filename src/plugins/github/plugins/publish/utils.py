import re

from githubkit.exception import RequestFailed
from nonebot import logger

from src.plugins.github import plugin_config
from src.plugins.github.constants import (
    ISSUE_FIELD_PATTERN,
    ISSUE_FIELD_TEMPLATE,
    PUBLISH_LABEL,
)
from src.plugins.github.depends.utils import get_type_by_labels
from src.plugins.github.handlers import GithubHandler, IssueHandler
from src.plugins.github.typing import PullRequestList
from src.plugins.github.utils import commit_message as _commit_message
from src.providers.models import RegistryUpdatePayload, to_store
from src.providers.utils import dump_json5, load_json_from_file
from src.providers.validation import PublishType, ValidationDict

from .constants import (
    BRANCH_NAME_PREFIX,
    COMMIT_MESSAGE_PREFIX,
    PLUGIN_STRING_LIST,
    PLUGIN_TEST_BUTTON_IN_PROGRESS_STRING,
    PLUGIN_TEST_BUTTON_STRING,
    PLUGIN_TEST_PATTERN,
    PLUGIN_TEST_STRING,
)
from .validation import (
    validate_adapter_info_from_issue,
    validate_bot_info_from_issue,
    validate_plugin_info_from_issue,
)


def get_type_by_title(title: str) -> PublishType | None:
    """通过标题获取类型"""
    if title.startswith(f"{PublishType.BOT.value}:"):
        return PublishType.BOT
    if title.startswith(f"{PublishType.PLUGIN.value}:"):
        return PublishType.PLUGIN
    if title.startswith(f"{PublishType.ADAPTER.value}:"):
        return PublishType.ADAPTER


def get_type_by_commit_message(message: str) -> PublishType | None:
    """通过提交信息获取类型"""
    if message.startswith(f"{COMMIT_MESSAGE_PREFIX} {PublishType.BOT.value.lower()}"):
        return PublishType.BOT
    if message.startswith(
        f"{COMMIT_MESSAGE_PREFIX} {PublishType.PLUGIN.value.lower()}"
    ):
        return PublishType.PLUGIN
    if message.startswith(
        f"{COMMIT_MESSAGE_PREFIX} {PublishType.ADAPTER.value.lower()}"
    ):
        return PublishType.ADAPTER


def commit_message(type: PublishType, name: str, issue_number: int) -> str:
    """构造提交信息"""
    return _commit_message(
        COMMIT_MESSAGE_PREFIX, f"{type.value.lower()} {name}", issue_number
    )


def extract_issue_number_from_ref(ref: str) -> int | None:
    """从 Ref 中提取议题号"""
    match = re.search(rf"{BRANCH_NAME_PREFIX}(\d+)", ref)
    if match:
        return int(match.group(1))


def extract_name_from_title(title: str, publish_type: PublishType) -> str | None:
    """从标题中提取名称"""
    match = re.search(rf"{publish_type.value}: (.+)", title)
    if match:
        return match.group(1)


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

        publish_type = get_type_by_labels(pull.labels)
        issue_handler = await handler.to_issue_handler(issue_number)

        if publish_type:
            # 重新测试
            match publish_type:
                case PublishType.ADAPTER:
                    result = await validate_adapter_info_from_issue(issue_handler.issue)
                case PublishType.BOT:
                    result = await validate_bot_info_from_issue(issue_handler.issue)
                case PublishType.PLUGIN:
                    result = await validate_plugin_info_from_issue(issue_handler)
                case _:
                    raise ValueError("暂不支持的发布类型")

            # 如果信息验证失败，则跳过更新
            if not result.valid:
                logger.error("信息验证失败，已跳过")
                logger.error(f"验证结果: {result}")
                continue

            # 每次切换前都要确保回到主分支
            handler.checkout_branch(plugin_config.input_config.base, update=True)
            # 切换到对应分支
            handler.switch_branch(pull.head.ref)
            # 更新文件
            update_file(result)

            message = commit_message(result.type, result.name, issue_number)
            issue_handler.commit_and_push(message, pull.head.ref)

            logger.info("拉取请求更新完毕")


def update_file(result: ValidationDict) -> None:
    """更新文件"""
    assert result.valid
    assert result.info
    new_data = to_store(result.info)

    match result.type:
        case PublishType.ADAPTER:
            path = plugin_config.input_config.adapter_path
        case PublishType.BOT:
            path = plugin_config.input_config.bot_path
        case PublishType.PLUGIN:
            path = plugin_config.input_config.plugin_path
        case _:
            raise ValueError("暂不支持的发布类型")

    logger.info(f"正在更新文件: {path}")

    data = load_json_from_file(path)
    data.append(new_data)
    dump_json5(path, data)

    logger.info("文件更新完成")


async def ensure_issue_content(handler: IssueHandler):
    """确保议题内容中包含所需的插件信息"""
    new_content = []
    issue_body = handler.issue.body or ""

    for name in PLUGIN_STRING_LIST:
        pattern = re.compile(ISSUE_FIELD_PATTERN.format(name))
        if not pattern.search(issue_body):
            new_content.append(ISSUE_FIELD_TEMPLATE.format(name))

    if new_content:
        new_content.append(issue_body)
        await handler.update_issue_body("\n\n".join(new_content))
        logger.info("检测到议题内容缺失，已更新")


async def ensure_issue_plugin_test_button(handler: IssueHandler):
    """确保议题内容中包含插件测试按钮"""
    issue_body = handler.issue.body or ""

    new_content = f"{ISSUE_FIELD_TEMPLATE.format(PLUGIN_TEST_STRING)}\n\n{PLUGIN_TEST_BUTTON_STRING}"

    match = PLUGIN_TEST_PATTERN.search(issue_body)
    if not match:
        new_content = f"{issue_body}\n\n{new_content}"
        logger.info("为议题添加插件重测按钮")
    else:
        new_content = PLUGIN_TEST_PATTERN.sub(new_content, issue_body)
        logger.info("重置插件重测按钮文本")

    await handler.update_issue_body(new_content)


async def ensure_issue_plugin_test_button_in_progress(handler: IssueHandler):
    """确保议题内容中包含插件测试进行中的提示"""
    issue_body = handler.issue.body or ""

    new_content = f"{ISSUE_FIELD_TEMPLATE.format(PLUGIN_TEST_STRING)}\n\n{PLUGIN_TEST_BUTTON_IN_PROGRESS_STRING}"

    match = PLUGIN_TEST_PATTERN.search(issue_body)
    if not match:
        new_content = f"{issue_body}\n\n{new_content}"
        logger.info("为议题添加插件测试进行中的提示")
    else:
        new_content = PLUGIN_TEST_PATTERN.sub(new_content, issue_body)
        logger.info("重置插件测试进行中文本")

    await handler.update_issue_body(new_content)


async def process_pull_request(
    handler: IssueHandler, result: ValidationDict, branch_name: str, title: str
):
    """根据发布信息合法性创建拉取请求或将请求改为草稿"""
    if not result.valid:
        # 如果之前已经创建了拉取请求，则将其转换为草稿
        await handler.draft_pull_request(branch_name)
        return

    # 更新文件
    handler.switch_branch(branch_name)
    update_file(result)

    # 只有当远程分支不存在时才创建拉取请求
    # 需要在 commit_and_push 前判断，否则远程一定存在
    remote_branch_exists = handler.remote_branch_exists(branch_name)

    commit_message = f"{COMMIT_MESSAGE_PREFIX} {result.type.value.lower()} {result.name} (#{handler.issue_number})"
    handler.commit_and_push(commit_message, branch_name, handler.author)

    if not remote_branch_exists:
        # 创建拉取请求
        try:
            pull_number = await handler.create_pull_request(
                plugin_config.input_config.base,
                title,
                branch_name,
            )
            await handler.add_labels(pull_number, [PUBLISH_LABEL, result.type.value])
            return
        except RequestFailed:
            logger.info("该分支的拉取请求已创建，请前往查看")
    else:
        logger.info("远程分支已存在，跳过创建拉取请求")

    # 如果之前已经创建了拉取请求，则将其转换为可评审
    await handler.update_pull_request_status(title, branch_name)


async def trigger_registry_update(handler: IssueHandler, publish_type: PublishType):
    """通过 repository_dispatch 触发商店列表更新"""
    issue = handler.issue

    # 重新验证信息
    # 这个时候已经合并了发布信息，如果还加载之前的数据则会报错重复
    # 所以这里不能加载之前的数据
    match publish_type:
        case PublishType.ADAPTER:
            result = await validate_adapter_info_from_issue(
                issue, load_previous_data=False
            )
        case PublishType.BOT:
            result = await validate_bot_info_from_issue(issue, load_previous_data=False)
        case PublishType.PLUGIN:
            result = await validate_plugin_info_from_issue(
                handler, load_previous_data=False
            )
        case _:
            raise ValueError("暂不支持的发布类型")

    if not result.valid or not result.info:
        logger.error("信息验证失败，跳过触发商店列表更新")
        logger.debug(f"验证结果: {result}")
        return

    # 触发商店列表更新
    await handler.create_dispatch_event(
        event_type="registry_update",
        client_payload=RegistryUpdatePayload.from_info(result.info).model_dump(),
        repo=plugin_config.input_config.registry_repository,
    )
    logger.info("已触发商店列表更新")
