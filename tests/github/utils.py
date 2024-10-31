import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from githubkit.rest import Issue
from pytest_mock import MockFixture


def generate_issue_body_adapter(
    name: str = "name",
    desc: str = "desc",
    module_name: str = "module_name",
    project_link: str = "project_link",
    homepage: str = "https://nonebot.dev",
    tags: list = [{"label": "test", "color": "#ffffff"}],
):
    return f"""### 适配器名称\n\n{name}\n\n### 适配器描述\n\n{desc}\n\n### PyPI 项目名\n\n{project_link}\n\n### 适配器 import 包名\n\n{module_name}\n\n### 适配器项目仓库/主页链接\n\n{homepage}\n\n### 标签\n\n{json.dumps(tags)}"""


def generate_issue_body_bot(
    name: str = "name",
    desc: str = "desc",
    homepage: str = "https://nonebot.dev",
    tags: list | str = [{"label": "test", "color": "#ffffff"}],
):
    if isinstance(tags, list):
        tags = json.dumps(tags)
    return f"""### 机器人名称\n\n{name}\n\n### 机器人描述\n\n{desc}\n\n### 机器人项目仓库/主页链接\n\n{homepage}\n\n### 标签\n\n{tags}"""


def generate_issue_body_plugin(
    module_name: str = "module_name",
    project_link: str = "project_link",
    tags: list = [{"label": "test", "color": "#ffffff"}],
    config: str = "log_level=DEBUG",
):
    return f"""### PyPI 项目名\n\n{project_link}\n\n### 插件 import 包名\n\n{module_name}\n\n### 标签\n\n{json.dumps(tags)}\n\n### 插件配置项\n\n```dotenv\n{config}\n```"""


def generate_issue_body_plugin_skip_test(
    name: str = "name",
    desc: str = "desc",
    module_name: str = "module_name",
    project_link: str = "project_link",
    homepage: str = "https://nonebot.dev",
    tags: list = [{"label": "test", "color": "#ffffff"}],
    type: str = "application",
    supported_adapters: list[str] = ["~onebot.v11"],
    config: str = "log_level=DEBUG",
):
    return f"""### 插件名称\n\n{name}\n\n### 插件描述\n\n{desc}\n\n### PyPI 项目名\n\n{project_link}\n\n### 插件 import 包名\n\n{module_name}\n\n### 插件项目仓库/主页链接\n\n{homepage}\n\n### 标签\n\n{json.dumps(tags)}\n\n### 插件类型\n\n{type}\n\n### 插件支持的适配器\n\n{json.dumps(supported_adapters)}\n\n### 插件配置项\n\n```dotenv\n{config}\n```"""


def generate_issue_body_plugin_test_button(body: str, selected: bool):
    return f"""{body}\n\n### 插件测试\n\n- [{'x' if selected else ' '}] 单击左侧按钮重新测试，完成时勾选框将被选中"""


def generate_issue_body_remove(
    type: Literal["Plugin", "Adapter", "Bot"], key: str = "https://nonebot.dev"
):
    match type:
        case "Plugin":
            return """### PyPI 项目名\n\n{}\n\n### import 包名\n\n{}""".format(
                *key.split(":", 1)
            )
        case "Bot":
            return (
                """### 机器人名称\n\n{}\n\n### 机器人项目仓库/主页链接\n\n{}""".format(
                    *key.split(":", 1)
                )
            )
        case "Adapter":
            return f"""### 项目主页\n\n{key}"""


# def generate_issue_body_remove(homepage: str = "https://nonebot.dev"):
#     return f"""### 项目主页\n\n{homepage}"""


def check_json_data(file: Path, data: Any) -> None:
    with open(file) as f:
        assert json.load(f) == data


@dataclass
class MockBody:
    type: Literal["bot", "adapter", "plugin"]
    name: str = "name"
    desc: str = "desc"
    homepage: str = "https://nonebot.dev"
    tags: list = field(default_factory=lambda: [{"label": "test", "color": "#ffffff"}])

    module_name: str = "module_name"
    project_link: str = "project_link"

    skip: bool = False
    plugin_type: str = "application"
    supported_adapters: list[str] = field(default_factory=lambda: ["~onebot.v11"])
    config: str = "log_level=DEBUG"

    def generate(self):
        match self.type:
            case "bot":
                return generate_issue_body_bot(
                    name=self.name,
                    desc=self.desc,
                    homepage=self.homepage,
                    tags=self.tags,
                )
            case "adapter":
                return generate_issue_body_adapter(
                    name=self.name,
                    desc=self.desc,
                    module_name=self.module_name,
                    project_link=self.project_link,
                    homepage=self.homepage,
                    tags=self.tags,
                )
            case "plugin":
                if self.skip:
                    return generate_issue_body_plugin_skip_test(
                        name=self.name,
                        desc=self.desc,
                        module_name=self.module_name,
                        project_link=self.project_link,
                        homepage=self.homepage,
                        tags=self.tags,
                        type=self.plugin_type,
                        supported_adapters=self.supported_adapters,
                        config=self.config,
                    )
                return generate_issue_body_plugin(
                    module_name=self.module_name,
                    project_link=self.project_link,
                    tags=self.tags,
                    config=self.config,
                )


@dataclass
class MockUser:
    login: str = "test"
    id: int = 1


@dataclass
class MockIssue:
    number: int = 80
    title: str = "Bot: test"
    state: Literal["open", "closed"] = "open"
    body: str = field(default_factory=lambda: MockBody("bot").generate())
    pull_request: Any = None
    user: MockUser = field(default_factory=MockUser)

    def as_mock(self, mocker: MockFixture):
        mocker_issue = mocker.MagicMock(spec=Issue)
        mocker_issue.configure_mock(**self.__dict__)

        return mocker_issue


def get_github_bot(ctx):
    from typing import cast

    from nonebot import get_adapter
    from nonebot.adapters.github import Adapter, GitHubBot
    from nonebot.adapters.github.config import GitHubApp

    adapter = get_adapter(Adapter)
    bot = ctx.create_bot(
        base=GitHubBot,
        adapter=adapter,
        self_id=GitHubApp(app_id="1", private_key="1"),  # type: ignore
    )
    bot = cast(GitHubBot, bot)
    return adapter, bot


def get_issue_labels(labels: list[str]):
    from githubkit.rest import WebhookIssuesOpenedPropIssuePropLabelsItems as Label

    return [
        Label.model_construct(
            **{
                "color": "2AAAAA",
                "default": False,
                "description": "",
                "id": 27980759601,
                "name": label,
                "node_id": "MDU6TGFiZWwyNzk4MDc1OTY2",
                "url": f"https://api.github.com/repos/he0119/action-test/labels/{label}",
            }
        )
        for label in labels
    ]
