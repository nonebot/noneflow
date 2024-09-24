import asyncio
import json
import re
from typing import TYPE_CHECKING

from githubkit.typing import Missing
from nonebot import logger
from nonebot.adapters.github import Bot, GitHubBot

from src.plugins.github.models import GithubHandler, IssueHandler
from src.providers.validation import (
    PublishType,
    ValidationDict,
)
from src.plugins.github.depends import RepoInfo
from src.plugins.github.utils import dump_json, load_json, run_shell_command
from src.plugins.github.utils import commit_message as _commit_message
from src.plugins.github import plugin_config
from src.plugins.github.constants import ISSUE_FIELD_PATTERN, ISSUE_FIELD_TEMPLATE

from .validation import validate_plugin_info_from_issue

from .constants import (
    BRANCH_NAME_PREFIX,
    COMMIT_MESSAGE_PREFIX,
    PLUGIN_CONFIG_PATTERN,
    PLUGIN_MODULE_NAME_PATTERN,
    PLUGIN_STRING_LIST,
    PLUGIN_TEST_BUTTON_STRING,
    PLUGIN_TEST_BUTTON_PATTERN,
    PLUGIN_TEST_STRING,
    PROJECT_LINK_PATTERN,
    SKIP_PLUGIN_TEST_COMMENT,
)

if TYPE_CHECKING:
    from githubkit.rest import (
        Issue,
        PullRequest,
        PullRequestPropLabelsItems,
        PullRequestSimple,
        PullRequestSimplePropLabelsItems,
        WebhookIssueCommentCreatedPropIssueAllof0PropLabelsItems,
        WebhookIssuesEditedPropIssuePropLabelsItems,
        WebhookIssuesOpenedPropIssuePropLabelsItems,
        WebhookIssuesReopenedPropIssueMergedLabels,
        WebhookPullRequestReviewSubmittedPropPullRequestPropLabelsItems,
    )


def get_type_by_labels(
    labels: list["PullRequestPropLabelsItems"]
    | list["PullRequestSimplePropLabelsItems"]
    | list["WebhookPullRequestReviewSubmittedPropPullRequestPropLabelsItems"]
    | Missing[list["WebhookIssuesOpenedPropIssuePropLabelsItems"]]
    | Missing[list["WebhookIssuesReopenedPropIssueMergedLabels"]]
    | Missing[list["WebhookIssuesEditedPropIssuePropLabelsItems"]]
    | list["WebhookIssueCommentCreatedPropIssueAllof0PropLabelsItems"],
) -> PublishType | None:
    """通过标签获取类型"""
    if not labels:
        return None

    for label in labels:
        if isinstance(label, str):
            continue
        if label.name == PublishType.BOT.value:
            return PublishType.BOT
        if label.name == PublishType.PLUGIN.value:
            return PublishType.PLUGIN
        if label.name == PublishType.ADAPTER.value:
            return PublishType.ADAPTER


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
    handler: GithubHandler,
    pulls: list["PullRequestSimple"] | list["PullRequest"],
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

        if publish_type:
            # 需要先获取远程分支，否则无法切换到对应分支
            run_shell_command(["git", "fetch", "origin"])
            # 因为当前分支为触发处理冲突的分支，所以需要切换到每个拉取请求对应的分支
            run_shell_command(["git", "checkout", pull.head.ref])

            # 获取数据
            result = generate_validation_dict_from_file(
                publish_type,
                # 提交时的 commit message 中包含插件名称
                # 但因为仓库内的 plugins.json 中没有插件名称，所以需要从标题中提取
                extract_name_from_title(pull.title, publish_type)
                if publish_type == PublishType.PLUGIN
                else None,
            )

            # 回到主分支
            run_shell_command(["git", "checkout", plugin_config.input_config.base])
            # 切换到对应分支
            run_shell_command(["git", "switch", "-C", pull.head.ref])
            # 更新文件
            update_file(result)
            handler.commit_and_push(
                commit_message(result.type, result.name, issue_number),
                pull.head.ref,
                result.author,
            )
            logger.info("拉取请求更新完毕")


def generate_validation_dict_from_file(
    publish_type: PublishType,
    name: str | None = None,
) -> ValidationDict:
    """从文件中获取发布所需数据"""
    match publish_type:
        case PublishType.ADAPTER:
            with plugin_config.input_config.adapter_path.open(
                "r", encoding="utf-8"
            ) as f:
                data: list[dict[str, str]] = json.load(f)
            raw_data = data[-1]
        case PublishType.BOT:
            with plugin_config.input_config.bot_path.open("r", encoding="utf-8") as f:
                data: list[dict[str, str]] = json.load(f)
            raw_data = data[-1]
        case PublishType.PLUGIN:
            with plugin_config.input_config.plugin_path.open(
                "r", encoding="utf-8"
            ) as f:
                data: list[dict[str, str]] = json.load(f)
            raw_data = data[-1]
            assert name, "插件名称不能为空"
            raw_data["name"] = name

    return ValidationDict(
        valid=True,
        type=publish_type,
        name=raw_data["name"],
        author=raw_data["author"],
        data=raw_data,
        errors=[],
    )


def update_file(result: ValidationDict) -> None:
    """更新文件"""
    new_data = result.data
    match result.type:
        case PublishType.ADAPTER:
            path = plugin_config.input_config.adapter_path
        case PublishType.BOT:
            path = plugin_config.input_config.bot_path
        case PublishType.PLUGIN:
            path = plugin_config.input_config.plugin_path
            # nonebot2 仓库内只需要这部分数据
            new_data = {
                "module_name": new_data["module_name"],
                "project_link": new_data["project_link"],
                "author": new_data["author"],
                "tags": new_data["tags"],
                "is_official": new_data["is_official"],
            }

    logger.info(f"正在更新文件: {path}")

    data = load_json(path)
    data.append(new_data)
    dump_json(path, data, 2)

    logger.info("文件更新完成")


async def should_skip_plugin_test(
    bot: Bot,
    repo_info: RepoInfo,
    issue_number: int,
) -> bool:
    """判断评论是否包含跳过的标记"""
    comments = (
        await bot.rest.issues.async_list_comments(
            **repo_info.model_dump(), issue_number=issue_number
        )
    ).parsed_data
    for comment in comments:
        author_association = comment.author_association
        if comment.body == SKIP_PLUGIN_TEST_COMMENT and author_association in [
            "OWNER",
            "MEMBER",
        ]:
            return True
    return False


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
        await handler.update_issue_content(
            "\n\n".join(new_content),
        )
        logger.info("检测到议题内容缺失，已更新")


async def ensure_issue_test_button(handler: IssueHandler):
    """确保议题内容中包含插件重测按钮"""
    issue_body = handler.issue.body or ""

    search_result = PLUGIN_TEST_BUTTON_PATTERN.search(issue_body)
    if not search_result:
        new_content = f"{ISSUE_FIELD_TEMPLATE.format(PLUGIN_TEST_STRING)}\n\n{PLUGIN_TEST_BUTTON_STRING}"

        await handler.update_issue_content(f"{issue_body}\n\n{new_content}")
        logger.info("为议题添加插件重测按钮")
    elif search_result.group(1) == " ":
        new_content = issue_body.replace(
            search_result.group(0), PLUGIN_TEST_BUTTON_STRING
        )
        await handler.update_issue_content(f"{new_content}")
        logger.info("选中议题的插件测试按钮")


async def should_skip_plugin_publish(
    issue: "Issue",
) -> bool:
    """判断是否跳过插件测试"""
    body = issue.body if issue.body else ""
    search_result = PLUGIN_TEST_BUTTON_PATTERN.search(body)
    if search_result:
        return search_result.group(1) == "x"
    return False


async def process_pull_request(
    handler: IssueHandler,
    result: ValidationDict,
    branch_name: str,
    title: str,
):
    """
    根据发布信息合法性创建拉取请求或将请求改为草稿
    """
    if result.valid:
        commit_message = f"{COMMIT_MESSAGE_PREFIX} {result.type.value.lower()} {result.name} (#{handler.issue_number})"

        run_shell_command(["git", "switch", "-C", branch_name])
        # 更新文件
        update_file(result)
        handler.commit_and_push(commit_message, branch_name)
        # 创建拉取请求
        await handler.create_pull_request(
            plugin_config.input_config.base, title, branch_name, result.type.value
        )

    else:
        # 如果之前已经创建了拉取请求，则将其转换为草稿
        await handler.pull_request_to_draft(branch_name)


async def trigger_registry_update(
    bot: GitHubBot, repo_info: RepoInfo, publish_type: PublishType, issue: "Issue"
):
    """通过 repository_dispatch 触发商店列表更新"""
    if publish_type == PublishType.PLUGIN:
        config = PLUGIN_CONFIG_PATTERN.search(issue.body) if issue.body else ""
        # 插件测试是否被跳过
        plugin_config.skip_plugin_test = await should_skip_plugin_test(
            bot, repo_info, issue.number
        )
        if plugin_config.skip_plugin_test:
            # 重新从议题中获取数据，并验证，防止中间有人修改了插件信息
            # 因为此时已经将新插件的信息添加到插件列表中
            # 直接将插件列表变成空列表，避免重新验证时出现重复报错
            with plugin_config.input_config.plugin_path.open(
                "w", encoding="utf-8"
            ) as f:
                json.dump([], f)
            result = await validate_plugin_info_from_issue(issue)
            logger.debug(f"插件信息验证结果: {result}")
            if not result.valid:
                logger.error("插件信息验证失败，跳过触发商店列表更新")
                return

            client_payload = {
                "type": publish_type.value,
                "key": f"{result.data["project_link"]}:{result.data["module_name"]}",
                "config": config.group(1) if config else "",
                "data": json.dumps(result.data),
            }
        else:
            # 从议题中获取的插件信息
            # 这样如果在 json 更新后再次运行也不会获取到不属于该插件的信息
            body = issue.body if issue.body else ""
            module_name = PLUGIN_MODULE_NAME_PATTERN.search(body)
            project_link = PROJECT_LINK_PATTERN.search(body)
            config = PLUGIN_CONFIG_PATTERN.search(body)

            if not module_name or not project_link:
                logger.error("无法从议题中获取插件信息，跳过触发商店列表更新")
                return

            module_name = module_name.group(1)
            project_link = project_link.group(1)
            config = config.group(1) if config else ""

            client_payload = {
                "type": publish_type.value,
                "key": f"{project_link}:{module_name}",
                "config": config,
            }
    else:
        client_payload = {"type": publish_type.value}

    owner, repo = plugin_config.input_config.registry_repository.split("/")
    # GitHub 的缓存一般 2 分钟左右会刷新
    logger.info("准备触发商店列表更新，等待 5 分钟")
    await asyncio.sleep(300)
    # 触发商店列表更新
    await bot.rest.repos.async_create_dispatch_event(
        repo=repo,
        owner=owner,
        event_type="registry_update",
        client_payload=client_payload,  # type: ignore
    )
    logger.info("已触发商店列表更新")
