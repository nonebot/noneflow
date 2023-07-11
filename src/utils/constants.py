import re

NONEFLOW_MARKER = "<!-- NONEFLOW -->"

BOT_MARKER = "[bot]"
"""机器人的名字结尾都会带有这个"""

SKIP_PLUGIN_TEST_COMMENT = "/skip"

COMMENT_TITLE = "# 📃 商店发布检查结果"

COMMIT_MESSAGE_PREFIX = ":beers: publish"

BRANCH_NAME_PREFIX = "publish/issue"

TIPS_MESSAGE = (
    "💡 如需修改信息，请直接修改 issue，机器人会自动更新检查结果。\n💡 当插件加载测试失败时，请发布新版本后在当前页面下评论任意内容以触发测试。"
)

REUSE_MESSAGE = "♻️ 评论已更新至最新检查结果"

POWERED_BY_NONEFLOW_MESSAGE = (
    "💪 Powered by [NoneFlow](https://github.com/nonebot/noneflow)"
)

DETAIL_MESSAGE_TEMPLATE = (
    "<details><summary>详情</summary><pre><code>{detail_message}</code></pre></details>"
)

VALIDATION_MESSAGE_TEMPLATE = """> {publish_info}

**{result}**
{error_message}
{detail_message}
"""

COMMENT_MESSAGE_TEMPLATE = """{title}

{body}

---

{tips}

{footer}
"""

# PyPI 格式
PYPI_PACKAGE_NAME_PATTERN = re.compile(
    r"^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$",
    re.IGNORECASE,
)
# import 包名格式
PYTHON_MODULE_NAME_REGEX = re.compile(
    r"^([A-Z]|[A-Z][A-Z0-9._-]*[A-Z0-9])$",
    re.IGNORECASE,
)

MAX_NAME_LENGTH = 50
"""名称最大长度"""

# 匹配信息的正则表达式
# 格式：### {标题}\n\n{内容}
ISSUE_PATTERN = r"### {}\s+([^\s#].*?)(?=(?:\s+###|$))"
ISSUE_FIELD_TEMPLATE = "### {}"
ISSUE_FIELD_PATTERN = r"### {}\s+"

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
PLUGIN_VALID_TYPE = ["application", "library"]
"""插件类型当前只支持 application 和 library"""
# 协议
ADAPTER_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("适配器名称"))
ADAPTER_DESC_PATTERN = re.compile(ISSUE_PATTERN.format("适配器描述"))
ADAPTER_MODULE_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("适配器 import 包名"))
ADAPTER_HOMEPAGE_PATTERN = re.compile(ISSUE_PATTERN.format("适配器项目仓库/主页链接"))

# NoneBot Store
STORE_ADAPTERS_URL = "https://nonebot.dev/adapters.json"
