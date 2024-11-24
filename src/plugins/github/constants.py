NONEFLOW_MARKER = "<!-- NONEFLOW -->"

BRANCH_NAME_PREFIX = "publish/issue"

TITLE_MAX_LENGTH = 50
"""标题最大长度"""

# 匹配信息的正则表达式
# 格式：### {标题}\n\n{内容}
ISSUE_PATTERN = r"### {}\s+([^\s#].*?)(?=(?:\s+###|$))"
ISSUE_FIELD_TEMPLATE = "### {}"
ISSUE_FIELD_PATTERN = r"### {}\s+"

SKIP_COMMENT = "/skip"

REMOVE_LABEL = "Remove"
CONFIG_LABEL = "Config"
