import logging
from pathlib import Path
from typing import Optional

from github import Github
from pydantic import BaseModel, BaseSettings, SecretStr


class PartialGithubEventHeadCommit(BaseModel):
    message: str


class PartialGitHubEventIssue(BaseModel):
    number: int


class PartialGitHubEvent(BaseModel):
    action: Optional[str] = None
    issue: Optional[PartialGitHubEventIssue] = None
    pull_request: Optional[PartialGitHubEventIssue] = None
    head_commit: Optional[PartialGithubEventHeadCommit] = None


class Config(BaseModel):
    base: str
    plugin_path: str
    bot_path: str
    adapter_path: str


class Settings(BaseSettings):
    input_config: Config
    input_token: SecretStr
    github_repository: str
    github_event_path: Path
    github_event_name: Optional[str] = None


if __name__ == "__main__":
    FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=FORMAT)

    settings = Settings()
    logging.info(f"Using config: {settings.json()}")

    g = Github(settings.input_token.get_secret_value())
    repo = g.get_repo(settings.github_repository)

    github_event: Optional[PartialGitHubEvent] = None
    if settings.github_event_path.is_file():
        contents = settings.github_event_path.read_text()
        github_event = PartialGitHubEvent.parse_raw(contents)
        logging.info(f"Using github event: {github_event.json()}")
    else:
        logging.info(f"No github event file found at {settings.github_event_path}")
