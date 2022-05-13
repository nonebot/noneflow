import logging

from github import Github

import src.globals as g
from src.models import Settings
from src.process import process_issues_event, process_pull_request_event


def main():
    FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=FORMAT)

    g.settings = Settings()  # type: ignore
    logging.info(f"当前配置: {g.settings.json()}")

    if not g.settings.input_token.get_secret_value():
        logging.info("无法获得 Token，跳过此次操作")
        return

    github = Github(g.settings.input_token.get_secret_value())
    repo = github.get_repo(g.settings.github_repository)

    if not g.settings.github_event_path.is_file():
        logging.error(f"没有在 {g.settings.github_event_path} 找到 GitHub 事件文件")
        return

    if g.settings.github_event_name in ["pull_request", "pull_request_target"]:
        process_pull_request_event(repo)
    elif g.settings.github_event_name == "issues":
        process_issues_event(repo)
    else:
        logging.info(f"不支持的事件: {g.settings.github_event_name}，已跳过")


if __name__ == "__main__":
    main()
