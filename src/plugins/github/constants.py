NONEFLOW_MARKER = "<!-- NONEFLOW -->"

BOT_MARKER = "[bot]"
"""机器人的名字结尾都会带有这个"""

SKIP_PLUGIN_TEST_COMMENT = "/skip"

BRANCH_NAME_PREFIX = "publish/issue"

TITLE_MAX_LENGTH = 50
"""标题最大长度"""

# 匹配信息的正则表达式
# 格式：### {标题}\n\n{内容}
ISSUE_PATTERN = r"### {}\s+([^\s#].*?)(?=(?:\s+###|$))"
ISSUE_FIELD_TEMPLATE = "### {}"
ISSUE_FIELD_PATTERN = r"### {}\s+"

SKIP_COMMENT = "/skip"
