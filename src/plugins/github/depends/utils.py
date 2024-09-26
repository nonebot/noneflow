import re


def extract_issue_number_from_ref(ref: str) -> int | None:
    """从 Ref 中提取议题号"""
    match = re.search(r"(\w{4,10})\/issue(\d+)", ref)
    if match:
        return int(match.group(2))
