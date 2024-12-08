import re

from src.plugins.github.constants import ISSUE_PATTERN

# Bot
REMOVE_BOT_HOMEPAGE_PATTERN = re.compile(
    ISSUE_PATTERN.format("机器人项目仓库/主页链接")
)
REMOVE_BOT_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("机器人名称"))
# Plugin
REMOVE_PLUGIN_PROJECT_LINK_PATTERN = re.compile(ISSUE_PATTERN.format("PyPI 项目名"))
REMOVE_PLUGIN_MODULE_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("import 包名"))
# Driver / Adapter
REMOVE_HOMEPAGE_PATTERN = re.compile(ISSUE_PATTERN.format("项目主页"))

BRANCH_NAME_PREFIX = "remove/issue"

COMMIT_MESSAGE_PREFIX = ":hammer: remove"
