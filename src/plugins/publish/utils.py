import json
import re
import subprocess
from typing import TYPE_CHECKING, Union

from githubkit.exception import RequestFailed
from githubkit.rest.models import PullRequest, PullRequestSimple
from nonebot import logger
from nonebot.adapters.github import Bot, GitHubBot

from src.utils.validation import PublishType, ValidationDict, validate_info

from .config import plugin_config
from .constants import (
    ADAPTER_DESC_PATTERN,
    ADAPTER_HOMEPAGE_PATTERN,
    ADAPTER_MODULE_NAME_PATTERN,
    ADAPTER_NAME_PATTERN,
    BOT_DESC_PATTERN,
    BOT_HOMEPAGE_PATTERN,
    BOT_NAME_PATTERN,
    BRANCH_NAME_PREFIX,
    COMMIT_MESSAGE_PREFIX,
    ISSUE_FIELD_PATTERN,
    ISSUE_FIELD_TEMPLATE,
    NONEFLOW_MARKER,
    PLUGIN_CONFIG_PATTERN,
    PLUGIN_DESC_PATTERN,
    PLUGIN_HOMEPAGE_PATTERN,
    PLUGIN_MODULE_NAME_PATTERN,
    PLUGIN_NAME_PATTERN,
    PLUGIN_STRING_LIST,
    PLUGIN_SUPPORTED_ADAPTERS_PATTERN,
    PLUGIN_TYPE_PATTERN,
    PROJECT_LINK_PATTERN,
    SKIP_PLUGIN_TEST_COMMENT,
    TAGS_PATTERN,
)
from .models import RepoInfo
from .render import render_comment

if TYPE_CHECKING:
    from githubkit.rest.models import Issue, IssuePropLabelsItemsOneof1, Label
    from githubkit.webhooks.models import Issue as WebhookIssue
    from githubkit.webhooks.models import (
        IssueCommentCreatedPropIssue,
        IssuesOpenedPropIssue,
        IssuesReopenedPropIssue,
    )
    from githubkit.webhooks.models import Label as WebhookLabel
    from githubkit.webhooks.models import PullRequestClosedPropPullRequest


def run_shell_command(command: list[str]):
    """运行 shell 命令

    如果遇到错误则抛出异常
    """
    logger.info(f"运行命令: {command}")
    try:
        r = subprocess.run(command, check=True, capture_output=True)
        logger.debug(f"命令输出: \n{r.stdout.decode()}")
    except subprocess.CalledProcessError as e:
        logger.debug("命令运行失败")
        logger.debug(f"命令输出: \n{e.stdout.decode()}")
        logger.debug(f"命令错误: \n{e.stderr.decode()}")
        raise
    return r


def get_type_by_labels(
    labels: list["Label"]
    | list["WebhookLabel"]
    | list[Union[str, "IssuePropLabelsItemsOneof1"]],
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


def commit_and_push(result: ValidationDict, branch_name: str, issue_number: int):
    """提交并推送"""
    commit_message = f"{COMMIT_MESSAGE_PREFIX} {result['type'].value.lower()} {result['name']} (#{issue_number})"

    run_shell_command(["git", "config", "--global", "user.name", result["author"]])
    user_email = f"{result['author']}@users.noreply.github.com"
    run_shell_command(["git", "config", "--global", "user.email", user_email])
    run_shell_command(["git", "add", "-A"])
    try:
        run_shell_command(["git", "commit", "-m", commit_message])
    except:
        # 如果提交失败，因为是 pre-commit hooks 格式化代码导致的，所以需要再次提交
        run_shell_command(["git", "add", "-A"])
        run_shell_command(["git", "commit", "-m", commit_message])

    try:
        run_shell_command(["git", "fetch", "origin"])
        r = run_shell_command(["git", "diff", f"origin/{branch_name}", branch_name])
        if r.stdout:
            raise Exception
        else:
            logger.info("检测到本地分支与远程分支一致，跳过推送")
    except:
        logger.info("检测到本地分支与远程分支不一致，尝试强制推送")
        run_shell_command(["git", "push", "origin", branch_name, "-f"])


def extract_issue_number_from_ref(ref: str) -> int | None:
    """从 Ref 中提取议题号"""
    match = re.search(rf"{BRANCH_NAME_PREFIX}(\d+)", ref)
    if match:
        return int(match.group(1))


def validate_info_from_issue(
    issue: "IssuesOpenedPropIssue | IssuesReopenedPropIssue | IssueCommentCreatedPropIssue | Issue | WebhookIssue",
    publish_type: PublishType,
) -> ValidationDict:
    """从议题中提取发布所需数据"""
    body = issue.body if issue.body else ""

    match publish_type:
        case PublishType.ADAPTER:
            module_name = ADAPTER_MODULE_NAME_PATTERN.search(body)
            project_link = PROJECT_LINK_PATTERN.search(body)
            name = ADAPTER_NAME_PATTERN.search(body)
            desc = ADAPTER_DESC_PATTERN.search(body)
            author = issue.user.login if issue.user else None
            homepage = ADAPTER_HOMEPAGE_PATTERN.search(body)
            tags = TAGS_PATTERN.search(body)
            with plugin_config.input_config.adapter_path.open(
                "r", encoding="utf-8"
            ) as f:
                data: list[dict[str, str]] = json.load(f)

            raw_data = {
                "module_name": module_name.group(1).strip() if module_name else None,
                "project_link": project_link.group(1).strip() if project_link else None,
                "name": name.group(1).strip() if name else None,
                "desc": desc.group(1).strip() if desc else None,
                "author": author,
                "homepage": homepage.group(1).strip() if homepage else None,
                "tags": tags.group(1).strip() if tags else None,
                "previous_data": data,
            }
        case PublishType.BOT:
            name = BOT_NAME_PATTERN.search(body)
            desc = BOT_DESC_PATTERN.search(body)
            author = issue.user.login if issue.user else None
            homepage = BOT_HOMEPAGE_PATTERN.search(body)
            tags = TAGS_PATTERN.search(body)

            raw_data = {
                "name": name.group(1).strip() if name else None,
                "desc": desc.group(1).strip() if desc else None,
                "author": author,
                "homepage": homepage.group(1).strip() if homepage else None,
                "tags": tags.group(1).strip() if tags else None,
            }
        case PublishType.PLUGIN:
            author = issue.user.login if issue.user else None
            module_name = PLUGIN_MODULE_NAME_PATTERN.search(body)
            project_link = PROJECT_LINK_PATTERN.search(body)
            tags = TAGS_PATTERN.search(body)
            module_name = module_name.group(1).strip() if module_name else None
            project_link = project_link.group(1).strip() if project_link else None
            tags = tags.group(1).strip() if tags else None
            with plugin_config.input_config.plugin_path.open(
                "r", encoding="utf-8"
            ) as f:
                data: list[dict[str, str]] = json.load(f)
            raw_data = {
                "module_name": module_name,
                "project_link": project_link,
                "author": author,
                "tags": tags,
                "skip_plugin_test": plugin_config.skip_plugin_test,
                "plugin_test_result": plugin_config.plugin_test_result,
                "plugin_test_output": plugin_config.plugin_test_output,
                "github_repository": plugin_config.github_repository,
                "github_run_id": plugin_config.github_run_id,
                "previous_data": data,
            }
            # 如果插件测试被跳过，则从议题中获取信息
            if plugin_config.skip_plugin_test:
                name = PLUGIN_NAME_PATTERN.search(body)
                desc = PLUGIN_DESC_PATTERN.search(body)
                homepage = PLUGIN_HOMEPAGE_PATTERN.search(body)
                type = PLUGIN_TYPE_PATTERN.search(body)
                supported_adapters = PLUGIN_SUPPORTED_ADAPTERS_PATTERN.search(body)

                if name:
                    raw_data["name"] = name.group(1).strip()
                if desc:
                    raw_data["desc"] = desc.group(1).strip()
                if homepage:
                    raw_data["homepage"] = homepage.group(1).strip()
                if type:
                    raw_data["type"] = type.group(1).strip()
                if supported_adapters:
                    raw_data["supported_adapters"] = supported_adapters.group(1).strip()
            elif plugin_config.plugin_test_metadata:
                raw_data["name"] = plugin_config.plugin_test_metadata.name
                raw_data["desc"] = plugin_config.plugin_test_metadata.description
                raw_data["homepage"] = plugin_config.plugin_test_metadata.homepage
                raw_data["type"] = plugin_config.plugin_test_metadata.type
                raw_data[
                    "supported_adapters"
                ] = plugin_config.plugin_test_metadata.supported_adapters
            else:
                # 插件缺少元数据
                # 可能为插件测试未通过，或者插件未按规范编写
                raw_data["name"] = project_link

    return validate_info(publish_type, raw_data)


async def resolve_conflict_pull_requests(
    bot: Bot,
    repo_info: RepoInfo,
    pulls: list[PullRequestSimple] | list[PullRequest],
):
    """根据关联的议题提交来解决冲突

    参考对应的议题重新更新对应分支
    """
    # 跳过插件测试，因为这个时候插件测试任务没有运行
    plugin_config.skip_plugin_test = True

    for pull in pulls:
        # 回到主分支
        run_shell_command(["git", "checkout", plugin_config.input_config.base])
        # 切换到对应分支
        run_shell_command(["git", "switch", "-C", pull.head.ref])

        issue_number = extract_issue_number_from_ref(pull.head.ref)
        if not issue_number:
            logger.error(f"无法获取 {pull.title} 对应的议题")
            return

        logger.info(f"正在处理 {pull.title}")
        issue = (
            await bot.rest.issues.async_get(
                **repo_info.dict(), issue_number=issue_number
            )
        ).parsed_data

        publish_type = get_type_by_labels(issue.labels)
        if publish_type:
            result = validate_info_from_issue(issue, publish_type)
            if result["valid"]:
                update_file(result)
                commit_and_push(result, pull.head.ref, issue_number)
                logger.info("拉取请求更新完毕")
            else:
                comment = await render_comment(result)
                logger.info(comment)
                logger.info("发布没通过检查，已跳过")


def update_file(result: ValidationDict) -> None:
    """更新文件"""
    match result["type"]:
        case PublishType.ADAPTER:
            path = plugin_config.input_config.adapter_path
        case PublishType.BOT:
            path = plugin_config.input_config.bot_path
        case PublishType.PLUGIN:
            path = plugin_config.input_config.plugin_path

    logger.info(f"正在更新文件: {path}")
    with path.open("r", encoding="utf-8") as f:
        data: list[dict[str, str]] = json.load(f)
    with path.open("w", encoding="utf-8") as f:
        # TODO: 以后换成 store 的格式
        data.append(result["data"])
        json.dump(data, f, ensure_ascii=False, indent=2)
        # 结尾加上换行符，不然会被 pre-commit fix
        f.write("\n")
    logger.info(f"文件更新完成")


async def should_skip_plugin_test(
    bot: Bot,
    repo_info: RepoInfo,
    issue_number: int,
) -> bool:
    """判断是否跳过插件测试"""
    comments = (
        await bot.rest.issues.async_list_comments(
            **repo_info.dict(), issue_number=issue_number
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


async def create_pull_request(
    bot: Bot,
    repo_info: RepoInfo,
    result: ValidationDict,
    branch_name: str,
    issue_number: int,
    title: str,
):
    """创建拉取请求

    同时添加对应标签
    内容关联上对应的议题
    """
    # 关联相关议题，当拉取请求合并时会自动关闭对应议题
    body = f"resolve #{issue_number}"

    try:
        # 创建拉取请求
        resp = await bot.rest.pulls.async_create(
            **repo_info.dict(),
            title=title,
            body=body,
            base=plugin_config.input_config.base,
            head=branch_name,
        )
        pull = resp.parsed_data
        # 自动给拉取请求添加标签
        await bot.rest.issues.async_add_labels(
            **repo_info.dict(), issue_number=pull.number, labels=[result["type"].value]
        )
        logger.info("拉取请求创建完毕")
    except RequestFailed:
        logger.info("该分支的拉取请求已创建，请前往查看")

        pull = (
            await bot.rest.pulls.async_list(
                **repo_info.dict(), head=f"{repo_info.owner}:{branch_name}"
            )
        ).parsed_data[0]
        if pull.title != title:
            await bot.rest.pulls.async_update(
                **repo_info.dict(), pull_number=pull.number, title=title
            )
            logger.info(f"拉取请求标题已修改为 {title}")


async def comment_issue(
    bot: Bot, repo_info: RepoInfo, issue_number: int, result: ValidationDict
):
    """在议题中发布评论"""
    logger.info("开始发布评论")

    # 重复利用评论
    # 如果发现之前评论过，直接修改之前的评论
    comments = (
        await bot.rest.issues.async_list_comments(
            **repo_info.dict(), issue_number=issue_number
        )
    ).parsed_data
    reusable_comment = next(
        filter(lambda x: NONEFLOW_MARKER in (x.body if x.body else ""), comments),
        None,
    )

    comment = await render_comment(result, bool(reusable_comment))
    if reusable_comment:
        logger.info(f"发现已有评论 {reusable_comment.id}，正在修改")
        if reusable_comment.body != comment:
            await bot.rest.issues.async_update_comment(
                **repo_info.dict(), comment_id=reusable_comment.id, body=comment
            )
            logger.info("评论修改完成")
        else:
            logger.info("评论内容无变化，跳过修改")
    else:
        await bot.rest.issues.async_create_comment(
            **repo_info.dict(), issue_number=issue_number, body=comment
        )
        logger.info("评论创建完成")


async def ensure_issue_content(
    bot: Bot, repo_info: RepoInfo, issue_number: int, issue_body: str
):
    """确保议题内容中包含所需的插件信息"""
    new_content = []

    for name in PLUGIN_STRING_LIST:
        pattern = re.compile(ISSUE_FIELD_PATTERN.format(name))
        if not pattern.search(issue_body):
            new_content.append(ISSUE_FIELD_TEMPLATE.format(name))

    if new_content:
        new_content.append(issue_body)
        await bot.rest.issues.async_update(
            **repo_info.dict(), issue_number=issue_number, body="\n\n".join(new_content)
        )
        logger.info("检测到议题内容缺失，已更新")


async def trigger_registry_update(
    bot: GitHubBot,
    publish_type: PublishType,
    pull: "PullRequestClosedPropPullRequest",
    issue: "Issue",
):
    """通过 repository_dispatch 触发商店列表更新"""
    if not pull.merged:
        logger.info("拉取请求未合并，跳过触发商店列表更新")
        return

    if publish_type == PublishType.PLUGIN:
        with plugin_config.input_config.plugin_path.open() as f:
            plugins = json.load(f)

        if not plugins:
            return

        plugin = plugins[-1]
        project_link = plugin["project_link"]
        module_name = plugin["module_name"]
        config = PLUGIN_CONFIG_PATTERN.search(issue.body) if issue.body else ""

        client_payload = {
            "type": publish_type.value,
            "key": f"{project_link}:{module_name}",
            "config": config.group(1) if config else "",
        }
    else:
        client_payload = {"type": publish_type.value}

    owner, repo = plugin_config.input_config.registry_repository.split("/")
    # 触发商店列表更新
    await bot.rest.repos.async_create_dispatch_event(
        repo=repo,
        owner=owner,
        event_type="registry_update",
        client_payload=client_payload,  # type: ignore
    )
    logger.info("已触发商店列表更新")
