from pathlib import Path

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

PUBLISH_LABEL = "Publish"
REMOVE_LABEL = "Remove"
CONFIG_LABEL = "Config"


ARTIFACT_PATH = Path("artifact")
if not ARTIFACT_PATH.exists():
    ARTIFACT_PATH.mkdir(parents=True)

REGISTRY_DATA_NAME = "registry_data.json"
"""通过 Artifact 传递数据的文件名"""

REGISTRY_DATA_PATH = ARTIFACT_PATH / REGISTRY_DATA_NAME
