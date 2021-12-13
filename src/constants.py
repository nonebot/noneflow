import re

COMMENT_TITLE = "📃 Publish Check Result"

COMMIT_MESSAGE_PREFIX = ":beers: publish"

BRANCH_NAME_PREFIX = "publish/issue"

REUSE_MESSAGE = "♻️ This comment has been updated with the latest result."

POWERED_BY_BOT_MESSAGE = "💪 Powered by NoneBot2 Publish Bot"

VALIDATION_MESSAGE_TEMPLATE = """> {publish_info}

**{result}**
{error_message}
{detail_message}
"""

COMMENT_MESSAGE_TEMPLATE = """# {title}

{body}

---

{footer}
"""

# 匹配信息的正则表达式
MODULE_NAME_PATTERN = re.compile(r"- module_name: (.+)")
PROJECT_LINK_PATTERN = re.compile(r"- project_link: (.+)")
NAME_PATTERN = re.compile(r"- name: (.+)")
DESC_PATTERN = re.compile(r"- desc: (.+)")
HOMEPAGE_PATTERN = re.compile(r"- homepage: (.+)")
TAGS_PATTERN = re.compile(r"- tags: (.+)")
IS_OFFICIAL_PATTERN = re.compile(r"- is_official: (.+)")
