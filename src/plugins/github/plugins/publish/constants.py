import re

from src.plugins.github.constants import ISSUE_PATTERN

COMMIT_MESSAGE_PREFIX = ":beers: publish"

BRANCH_NAME_PREFIX = "publish/issue"

# 基本信息
PROJECT_LINK_PATTERN = re.compile(ISSUE_PATTERN.format("PyPI 项目名"))
TAGS_PATTERN = re.compile(ISSUE_PATTERN.format("标签"))
# 机器人
BOT_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("机器人名称"))
BOT_DESC_PATTERN = re.compile(ISSUE_PATTERN.format("机器人描述"))
BOT_HOMEPAGE_PATTERN = re.compile(ISSUE_PATTERN.format("机器人项目仓库/主页链接"))
# 插件
PLUGIN_MODULE_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("插件 import 包名"))
PLUGIN_NAME_STRING = "插件名称"
PLUGIN_NAME_PATTERN = re.compile(ISSUE_PATTERN.format(PLUGIN_NAME_STRING))
PLUGIN_DESC_STRING = "插件描述"
PLUGIN_DESC_PATTERN = re.compile(ISSUE_PATTERN.format(PLUGIN_DESC_STRING))
PLUGIN_HOMEPAGE_STRING = "插件项目仓库/主页链接"
PLUGIN_HOMEPAGE_PATTERN = re.compile(ISSUE_PATTERN.format(PLUGIN_HOMEPAGE_STRING))
PLUGIN_TYPE_STRING = "插件类型"
PLUGIN_TYPE_PATTERN = re.compile(ISSUE_PATTERN.format(PLUGIN_TYPE_STRING))
PLUGIN_CONFIG_PATTERN = re.compile(r"### 插件配置项\s+```(?:\w+)?\s?([\s\S]*?)```")
PLUGIN_TEST_STRING = "插件测试"
PLUGIN_TEST_PATTERN = re.compile(ISSUE_PATTERN.format(PLUGIN_TEST_STRING))
PLUGIN_TEST_BUTTON_TIPS = "如需重新运行插件测试，请勾选左侧勾选框"
PLUGIN_TEST_BUTTON_STRING = f"- [ ] {PLUGIN_TEST_BUTTON_TIPS}"
PLUGIN_TEST_BUTTON_IN_PROGRESS_STRING = "- [x] 🔥插件测试中，请稍后"
PLUGIN_SUPPORTED_ADAPTERS_STRING = "插件支持的适配器"
PLUGIN_SUPPORTED_ADAPTERS_PATTERN = re.compile(
    ISSUE_PATTERN.format(PLUGIN_SUPPORTED_ADAPTERS_STRING)
)
PLUGIN_STRING_LIST = [
    PLUGIN_NAME_STRING,
    PLUGIN_DESC_STRING,
    PLUGIN_HOMEPAGE_STRING,
    PLUGIN_TYPE_STRING,
    PLUGIN_SUPPORTED_ADAPTERS_STRING,
]
# 协议
ADAPTER_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("适配器名称"))
ADAPTER_DESC_PATTERN = re.compile(ISSUE_PATTERN.format("适配器描述"))
ADAPTER_MODULE_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("适配器 import 包名"))
ADAPTER_HOMEPAGE_PATTERN = re.compile(ISSUE_PATTERN.format("适配器项目仓库/主页链接"))

# 评论卡片模板
COMMENT_CARD_TEMPLATE = """[![{name}](https://img.shields.io/badge/{head}-{content}-{color}?style=for-the-badge)]({url})"""

# 发布信息项对应的中文名
LOC_NAME_MAP = {
    "name": "名称",
    "desc": "描述",
    "project_link": "PyPI 项目名",
    "module_name": "import 包名",
    "tags": "标签",
    "homepage": "项目仓库/主页链接",
    "type": "插件类型",
    "supported_adapters": "插件支持的适配器",
    "metadata": "插件测试元数据",
    "load": "插件是否成功加载",
    "version": "版本号",
    "time": "发布时间",
}
