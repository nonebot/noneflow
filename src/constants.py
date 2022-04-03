import re

PUBLISH_BOT_MARKER = "<!-- PUBLISH_BOT -->"

COMMENT_TITLE = "# 📃 商店发布检查结果"

COMMIT_MESSAGE_PREFIX = ":beers: publish"

BRANCH_NAME_PREFIX = "publish/issue"

REUSE_MESSAGE = "♻️ 评论已更新至最新检查结果"

POWERED_BY_BOT_MESSAGE = "💪 Powered by NoneBot2 Publish Bot"

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

{footer}
"""

# 匹配信息的正则表达式
ISSUE_PATTERN = r"\*\*{}：\*\*\s+([^\s*].*?)(?=(?:\s+\*\*|$))"
# 基本信息
PROJECT_LINK_PATTERN = re.compile(ISSUE_PATTERN.format("PyPI 项目名"))
TAGS_PATTERN = re.compile(ISSUE_PATTERN.format("标签"))
# 机器人
BOT_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("机器人名称"))
BOT_DESC_PATTERN = re.compile(ISSUE_PATTERN.format("机器人功能"))
BOT_HOMEPAGE_PATTERN = re.compile(ISSUE_PATTERN.format("机器人项目仓库/主页链接"))
# 插件
PLUGIN_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("插件名称"))
PLUGIN_DESC_PATTERN = re.compile(ISSUE_PATTERN.format("插件功能"))
PLUGIN_MODULE_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("插件 import 包名"))
PLUGIN_HOMEPAGE_PATTERN = re.compile(ISSUE_PATTERN.format("插件项目仓库/主页链接"))
# 协议
ADAPTER_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("协议名称"))
ADAPTER_DESC_PATTERN = re.compile(ISSUE_PATTERN.format("协议功能"))
ADAPTER_MODULE_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("协议 import 包名"))
ADAPTER_HOMEPAGE_PATTERN = re.compile(ISSUE_PATTERN.format("协议项目仓库/主页链接"))
