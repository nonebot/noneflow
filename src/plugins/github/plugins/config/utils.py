from githubkit.exception import RequestFailed
from nonebot import logger

from src.plugins.github.constants import CONFIG_LABEL
from src.plugins.github.models import IssueHandler
from src.plugins.github.utils import run_shell_command
from src.providers.constants import PYPI_KEY_TEMPLATE
from src.providers.models import RegistryPlugin, StoreTestResult
from src.providers.utils import dump_json, load_json_from_file
from src.providers.validation import ValidationDict
from src.providers.validation.models import PluginPublishInfo

from .constants import COMMIT_MESSAGE_PREFIX, RESULTS_BRANCH


def update_file(result: ValidationDict) -> None:
    """更新文件"""
    if not isinstance(result.info, PluginPublishInfo):
        raise ValueError("仅支持修改插件配置")

    logger.info("正在更新配置文件和最新测试结果")

    # 读取文件
    previous_plugins: dict[str, RegistryPlugin] = {
        PYPI_KEY_TEMPLATE.format(
            project_link=plugin["project_link"], module_name=plugin["module_name"]
        ): RegistryPlugin(**plugin)
        for plugin in load_json_from_file("plugins.json")
    }
    previous_results: dict[str, StoreTestResult] = {
        key: StoreTestResult(**value)
        for key, value in load_json_from_file("results.json").items()
    }
    plugin_configs: dict[str, str] = load_json_from_file("plugin_configs.json")

    # 更新信息
    plugin = RegistryPlugin.from_publish_info(result.info)
    previous_plugins[plugin.key] = plugin
    previous_results[plugin.key] = StoreTestResult.from_info(result.info)
    plugin_configs[plugin.key] = result.info.test_config

    dump_json("plugins.json", list(previous_plugins.values()))
    dump_json("results.json", previous_results)
    dump_json("plugin_configs.json", plugin_configs, False)

    logger.info("文件更新完成")


async def process_pull_request(
    handler: IssueHandler, result: ValidationDict, branch_name: str, title: str
):
    """
    根据发布信息合法性创建拉取请求或将请求改为草稿
    """
    if result.valid:
        commit_message = f"{COMMIT_MESSAGE_PREFIX} {result.type.value.lower()} {result.name} (#{handler.issue_number})"

        # 需要先切换到结果分支
        run_shell_command(["git", "fetch", "origin", RESULTS_BRANCH])
        run_shell_command(["git", "checkout", RESULTS_BRANCH])
        # 创建新分支
        run_shell_command(["git", "switch", "-C", branch_name])
        # 更新文件
        update_file(result)
        handler.commit_and_push(commit_message, branch_name, handler.author)
        # 创建拉取请求
        try:
            await handler.create_pull_request(
                RESULTS_BRANCH,
                title,
                branch_name,
                [result.type.value, CONFIG_LABEL],
            )
        except RequestFailed:
            # 如果之前已经创建了拉取请求，则将其转换为草稿
            logger.info("该分支的拉取请求已创建，请前往查看")
            await handler.update_pull_request_status(title, branch_name)
    else:
        # 如果之前已经创建了拉取请求，则将其转换为草稿
        await handler.draft_pull_request(branch_name)
