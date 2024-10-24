import re

from src.plugins.github import plugin_config
from src.plugins.github.constants import ISSUE_PATTERN
from src.providers.validation.models import PublishType

REMOVE_HOMEPAGE_PATTERN = re.compile(ISSUE_PATTERN.format("项目主页"))

BRANCH_NAME_PREFIX = "remove/issue"

COMMIT_MESSAGE_PREFIX = ":hammer: remove"

REMOVE_LABEL = "Remove"

PUBLISH_PATH = {
    PublishType.PLUGIN: plugin_config.input_config.plugin_path,
    PublishType.ADAPTER: plugin_config.input_config.adapter_path,
    PublishType.BOT: plugin_config.input_config.bot_path,
}
