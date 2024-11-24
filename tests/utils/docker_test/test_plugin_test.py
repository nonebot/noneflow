import json
from pathlib import Path

from inline_snapshot import snapshot
from pytest_mock import MockerFixture


async def test_plugin_test(mocker: MockerFixture, tmp_path: Path):
    from src.providers.docker_test.plugin_test import PluginTest

    test = PluginTest("project_link:module_name", "test=123")

    mocker.patch.object(test, "_test_dir", tmp_path)

    def command_output(cmd: str, timeout: int = 300):
        if (
            cmd
            == r"""poetry init -n && sed -i "s/\^/~/g" pyproject.toml && poetry env info --ansi && poetry add project_link"""
        ):
            # create_poetry_project
            return (
                True,
                """
    Virtualenv
    Python:         3.12.7
    Implementation: CPython
    Path:           NA
    Executable:     NA

    Base
    Platform:   linux
    OS:         posix
    Python:     3.12.7
    Path:       /usr/local
    Executable: /usr/local/bin/python3.12
    Using version ^0.5.0 for nonebot-plugin-treehelp

    Updating dependencies
    Resolving dependencies...

    Package operations: 16 installs, 0 updates, 0 removals

      - Installing typing-extensions (4.12.2)
      - Installing annotated-types (0.7.0)
      - Installing idna (3.10)
      - Installing multidict (6.1.0)
      - Installing propcache (0.2.0)
      - Installing pydantic-core (2.23.4)
      - Installing sniffio (1.3.1)
      - Installing anyio (4.6.2.post1)
      - Installing exceptiongroup (1.2.2)
      - Installing loguru (0.7.2)
      - Installing pydantic (2.9.2)
      - Installing pygtrie (2.5.0)
      - Installing python-dotenv (1.0.1)
      - Installing yarl (1.17.2)
      - Installing nonebot2 (2.4.0)
      - Installing nonebot-plugin-treehelp (0.5.0)

    Writing lock file""",
                "",
            )
        if cmd == "poetry show project_link":
            # show_package_info
            return (
                True,
                """
    name         : nonebot-plugin-treehelp
     version      : 0.5.0
     description  : 适用于 Nonebot2 的树形帮助插件

    dependencies
     - nonebot2 >=2.2.0""",
                "",
            )
        if cmd == "poetry export --without-hashes":
            # show_plugin_dependencies
            return (
                True,
                """
nonebot2==2.4.0 ; python_version >= "3.9" and python_version < "4.0"
pydantic-core==2.27.0 ; python_version >= "3.9" and python_version < "4.0"
pydantic==2.10.0 ; python_version >= "3.9" and python_version < "4.0"
                    """,
                "",
            )
        if cmd == "poetry run python runner.py":
            # run_plugin_test
            with open(
                tmp_path / "project_link-module_name" / "metadata.json", "w"
            ) as f:
                json.dump(
                    {
                        "name": "帮助",
                        "desc": "获取插件帮助信息",
                        "usage": "获取插件列表 /help 获取插件树 /help -t /help --tree 获取某个插件的帮助 /help 插件名 获取某个插件的树 /help --tree 插件名",
                        "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
                        "type": "application",
                        "supported_adapters": None,
                    },
                    f,
                )
            return (True, "", "")

        raise ValueError(f"Unknown command: {cmd}")

    mocked_command = mocker.patch.object(test, "command")
    mocked_command.side_effect = command_output

    mocked_get_plugin_list = mocker.patch(
        "src.providers.docker_test.plugin_test.get_plugin_list"
    )
    mocked_get_plugin_list.return_value = {}

    result = await test.run()
    assert result == snapshot(
        {
            "metadata": {
                "name": "帮助",
                "desc": "获取插件帮助信息",
                "usage": "获取插件列表 /help 获取插件树 /help -t /help --tree 获取某个插件的帮助 /help 插件名 获取某个插件的树 /help --tree 插件名",
                "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
                "type": "application",
                "supported_adapters": None,
            },
            "outputs": [
                "项目 project_link 创建成功。",
                "    Virtualenv",
                "        Python:         3.12.7",
                "        Implementation: CPython",
                "        Path:           NA",
                "        Executable:     NA",
                "    ",
                "        Base",
                "        Platform:   linux",
                "        OS:         posix",
                "        Python:     3.12.7",
                "        Path:       /usr/local",
                "        Executable: /usr/local/bin/python3.12",
                "        Using version ^0.5.0 for nonebot-plugin-treehelp",
                "    ",
                "        Updating dependencies",
                "        Resolving dependencies...",
                "    ",
                "        Package operations: 16 installs, 0 updates, 0 removals",
                "    ",
                "          - Installing typing-extensions (4.12.2)",
                "          - Installing annotated-types (0.7.0)",
                "          - Installing idna (3.10)",
                "          - Installing multidict (6.1.0)",
                "          - Installing propcache (0.2.0)",
                "          - Installing pydantic-core (2.23.4)",
                "          - Installing sniffio (1.3.1)",
                "          - Installing anyio (4.6.2.post1)",
                "          - Installing exceptiongroup (1.2.2)",
                "          - Installing loguru (0.7.2)",
                "          - Installing pydantic (2.9.2)",
                "          - Installing pygtrie (2.5.0)",
                "          - Installing python-dotenv (1.0.1)",
                "          - Installing yarl (1.17.2)",
                "          - Installing nonebot2 (2.4.0)",
                "          - Installing nonebot-plugin-treehelp (0.5.0)",
                "    ",
                "        Writing lock file",
                "插件 project_link 的信息如下：",
                "    name         : nonebot-plugin-treehelp",
                "         version      : 0.5.0",
                "         description  : 适用于 Nonebot2 的树形帮助插件",
                "    ",
                "        dependencies",
                "         - nonebot2 >=2.2.0",
                "插件 project_link 依赖的插件如下：",
                "    ",
                "插件 module_name 加载正常：",
            ],
            "load": True,
            "run": True,
            "version": "0.5.0",
            "config": "test=123",
            "test_env": "python==3.12.7 nonebot2==2.4.0 pydantic==2.10.0",
        }
    )

    mocked_get_plugin_list.assert_called_once()
    mocked_command.assert_called()
