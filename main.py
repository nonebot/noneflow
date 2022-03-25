import logging

from github import Github

from src.models import Settings
from src.process import process_issues_event, process_pull_request_event


def main():
    FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=FORMAT)

    settings = Settings()  # type: ignore
    logging.info(f"当前配置: {settings.json()}")

    if not settings.input_token.get_secret_value():
        logging.info("无法获得 Token，跳过此次操作")
        return

    g = Github(settings.input_token.get_secret_value())
    repo = g.get_repo(settings.github_repository)

    if not settings.github_event_path.is_file():
        logging.error(f"没有在 {settings.github_event_path} 找到 GitHub 事件文件")
        return

    if settings.github_event_name == "pull_request":
        process_pull_request_event(settings, repo)
    elif settings.github_event_name == "issues":
        process_issues_event(settings, repo)
    else:
        logging.info(f"不支持的事件: {settings.github_event_name}，已跳过")


if __name__ == "__main__":
    main()
