import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict
from unittest.mock import MagicMock, call

import pyjson5
from githubkit.rest import Issue
from nonebug.mixin.call_api import ApiContext
from nonebug.mixin.process import MatcherContext
from pytest_mock import MockerFixture, MockFixture, MockType


class GitHubApi(TypedDict):
    api: str
    result: Any | None
    exception: NotRequired[Exception | None]


def should_call_apis(
    ctx: MatcherContext | ApiContext, apis: list[GitHubApi], data: list[Any]
) -> None:
    for n, api in enumerate(apis):
        ctx.should_call_api(**api, data=data[n])


def mock_subprocess_run_with_side_effect(
    mocker: MockerFixture, commands: dict[str, str] = {}
):
    def side_effect(*args, **kwargs):
        command_str = " ".join(args[0])
        if command_str in commands:
            value = MagicMock()
            value.stdout.decode.return_value = commands[command_str]
            return value
        # 默认返回远程分支不存在
        elif command_str.startswith("git ls-remote --heads origin"):
            value = MagicMock()
            value.stdout.decode.return_value = ""
            return value
        return MagicMock()

    mock_subprocess_run = mocker.patch("subprocess.run")
    mock_subprocess_run.side_effect = side_effect
    return mock_subprocess_run


def assert_subprocess_run_calls(mock: MockType, commands: list[list[str]]):
    calls = []
    for command in commands:
        calls.append(call(command, check=True, capture_output=True))

    mock.assert_has_calls(calls)


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
    return f"""### PyPI 项目名\n\n{project_link}\n\n### 插件模块名\n\n{module_name}\n\n### 标签\n\n{json.dumps(tags)}\n\n### 插件配置项\n\n```dotenv\n{config}\n```"""


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
    return f"""### 插件名称\n\n{name}\n\n### 插件描述\n\n{desc}\n\n### PyPI 项目名\n\n{project_link}\n\n### 插件模块名\n\n{module_name}\n\n### 插件项目仓库/主页链接\n\n{homepage}\n\n### 标签\n\n{json.dumps(tags)}\n\n### 插件类型\n\n{type}\n\n### 插件支持的适配器\n\n{json.dumps(supported_adapters)}\n\n### 插件配置项\n\n```dotenv\n{config}\n```"""


def generate_issue_body_plugin_test_button(body: str, selected: bool):
    from src.plugins.github.plugins.publish.constants import PLUGIN_TEST_BUTTON_TIPS

    return f"""{body}\n\n### 插件测试\n\n- [{"x" if selected else " "}] {PLUGIN_TEST_BUTTON_TIPS}"""


def generate_issue_body_remove(
    type: Literal["Plugin", "Adapter", "Bot", "Driver"],
    key: str = "https://nonebot.dev",
):
    match type:
        case "Bot":
            return (
                """### 机器人名称\n\n{}\n\n### 机器人项目仓库/主页链接\n\n{}""".format(
                    *key.split(":", 1)
                )
            )
        case _:
            return """### PyPI 项目名\n\n{}\n\n### import 包名\n\n{}""".format(
                *key.split(":", 1)
            )


def check_json_data(file: Path, data: Any) -> None:
    with open(file, encoding="utf-8") as f:
        assert pyjson5.decode_io(f) == data  # type: ignore


@dataclass
class MockBody:
    type: Literal["bot", "adapter", "plugin"]
    test_button: bool | None = None

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
                    body = generate_issue_body_plugin_skip_test(
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
                else:
                    body = generate_issue_body_plugin(
                        module_name=self.module_name,
                        project_link=self.project_link,
                        tags=self.tags,
                        config=self.config,
                    )
                if self.test_button is not None:
                    body = generate_issue_body_plugin_test_button(
                        body, self.test_button
                    )
                return body


@dataclass
class MockUser:
    login: str = "test"
    id: int = 1


@dataclass
class MockIssue:
    number: int = 80
    title: str = "Bot: test"
    state: Literal["open", "closed"] = "open"
    state_reason: None | Literal["completed", "reopened", "not_planned"] = None
    body: str = field(default_factory=lambda: MockBody("bot").generate())
    pull_request: Any = None
    user: MockUser = field(default_factory=MockUser)

    def as_mock(self, mocker: MockFixture | None = None):
        if mocker is None:
            mocker_issue = MagicMock(spec=Issue)
        else:
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
    bot = cast("GitHubBot", bot)
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
