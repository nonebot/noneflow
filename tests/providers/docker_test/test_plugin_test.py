import json
from pathlib import Path

from inline_snapshot import snapshot
from pytest_mock import MockerFixture


async def test_plugin_test(mocker: MockerFixture, tmp_path: Path):
    from src.providers.docker_test.plugin_test import PluginTest

    test = PluginTest("3.12", "project_link", "module_name", "test=123")

    mocker.patch.object(test, "_test_dir", tmp_path / "plugin_test")

    def command_output(cmd: str, timeout: int = 300):
        if (
            cmd
            == 'uv venv --python 3.12 && poetry init -n --python "~3.12" && poetry env info --ansi && poetry add project_link'
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
            with open(tmp_path / "plugin_test" / "metadata.json", "w") as f:
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
        if cmd == "poetry run python --version":
            return (True, "Python 3.12.7", "")

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
            "output": """\
项目 project_link 创建成功。
    Virtualenv
        Python:         3.12.7
        Implementation: CPython
        Path:           NA
        Executable:     NA
    \n\
        Base
        Platform:   linux
        OS:         posix
        Python:     3.12.7
        Path:       /usr/local
        Executable: /usr/local/bin/python3.12
        Using version ^0.5.0 for nonebot-plugin-treehelp
    \n\
        Updating dependencies
        Resolving dependencies...
    \n\
        Package operations: 16 installs, 0 updates, 0 removals
    \n\
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
    \n\
        Writing lock file
插件 project_link 的信息如下：
    name         : nonebot-plugin-treehelp
         version      : 0.5.0
         description  : 适用于 Nonebot2 的树形帮助插件
    \n\
        dependencies
         - nonebot2 >=2.2.0
插件 project_link 依赖的插件如下：
    \n\
插件 module_name 加载正常：\
""",
            "load": True,
            "run": True,
            "version": "0.5.0",
            "config": "test=123",
            "test_env": "python==3.12.7 nonebot2==2.4.0 pydantic==2.10.0",
        }
    )

    mocked_get_plugin_list.assert_called_once()
    mocked_command.assert_called()


async def test_plugin_test_dir_exists(mocker: MockerFixture, tmp_path: Path):
    """测试项目目录已存在的情况"""
    from src.providers.docker_test.plugin_test import PluginTest

    test = PluginTest("3.12", "project_link", "module_name")

    test_dir = tmp_path / "plugin_test"
    test_dir.mkdir()
    mocker.patch.object(test, "_test_dir", test_dir)

    # Mock command 函数
    async def mock_command(cmd: str, timeout: int = 300):  # noqa: ASYNC109
        if cmd == "poetry show project_link":
            return (
                True,
                """
name         : project_link
version      : 1.0.0
description  : A test plugin""",
                "",
            )
        if cmd == "poetry export --without-hashes":
            return (
                True,
                """
nonebot2==2.4.0 ; python_version >= "3.9"
pydantic==2.10.0 ; python_version >= "3.9"
""",
                "",
            )
        if cmd == "poetry run python --version":
            return (True, "Python 3.12.5", "")
        if cmd == "poetry run python runner.py":
            return (True, "", "")
        return (False, "", "")

    mocker.patch.object(test, "command", mock_command)
    mocker.patch(
        "src.providers.docker_test.plugin_test.get_plugin_list", return_value={}
    )

    result = await test.run()

    # 验证跳过创建
    assert "已存在，跳过创建" in result["output"]
    assert result["run"] is True
    assert result["load"] is True


async def test_plugin_test_create_failed(mocker: MockerFixture, tmp_path: Path):
    """测试项目创建失败的情况"""
    from src.providers.docker_test.plugin_test import PluginTest

    # 使用连字符格式的 project_link，因为 canonicalize_name 会将其转换为这种格式
    test = PluginTest("3.12", "project-link", "module_name")

    mocker.patch.object(test, "_test_dir", tmp_path / "plugin_test")

    # Mock command 函数，模拟创建失败
    async def mock_command(cmd: str, timeout: int = 300):  # noqa: ASYNC109
        if "poetry add" in cmd:
            return (
                False,
                "",
                """
Using version ^1.0.0 for project-link

Updating dependencies
Resolving dependencies... (error)
""",
            )
        return (False, "", "")

    mocker.patch.object(test, "command", mock_command)
    mocker.patch(
        "src.providers.docker_test.plugin_test.get_plugin_list", return_value={}
    )

    result = await test.run()

    # 验证创建失败
    assert "创建失败" in result["output"]
    assert result["run"] is False
    assert result["load"] is False
    # 应该从错误输出中提取版本号
    assert result["version"] == "1.0.0"


async def test_plugin_test_show_package_info_failed(
    mocker: MockerFixture, tmp_path: Path
):
    """测试获取插件信息失败的情况"""
    from src.providers.docker_test.plugin_test import PluginTest

    test = PluginTest("3.12", "project_link", "module_name")

    test_dir = tmp_path / "plugin_test"
    test_dir.mkdir()
    mocker.patch.object(test, "_test_dir", test_dir)

    async def mock_command(cmd: str, timeout: int = 300):  # noqa: ASYNC109
        if cmd == "poetry show project_link":
            return (False, "", "Error: package not found")
        if cmd == "poetry export --without-hashes":
            return (
                True,
                "nonebot2==2.4.0 ; python_version >= '3.9'",
                "",
            )
        if cmd == "poetry run python --version":
            return (True, "Python 3.12.5", "")
        if cmd == "poetry run python runner.py":
            return (True, "", "")
        return (True, "", "")

    mocker.patch.object(test, "command", mock_command)
    mocker.patch(
        "src.providers.docker_test.plugin_test.get_plugin_list", return_value={}
    )

    result = await test.run()

    # 验证信息获取失败
    assert "信息获取失败" in result["output"]


async def test_plugin_test_run_failed(mocker: MockerFixture, tmp_path: Path):
    """测试插件运行失败的情况"""
    from src.providers.docker_test.plugin_test import PluginTest

    test = PluginTest("3.12", "project_link", "module_name")

    test_dir = tmp_path / "plugin_test"
    test_dir.mkdir()
    mocker.patch.object(test, "_test_dir", test_dir)

    async def mock_command(cmd: str, timeout: int = 300):  # noqa: ASYNC109
        if cmd == "poetry show project_link":
            return (True, "version      : 1.0.0", "")
        if cmd == "poetry export --without-hashes":
            return (True, "nonebot2==2.4.0 ; python_version >= '3.9'", "")
        if cmd == "poetry run python --version":
            return (True, "Python 3.12.5", "")
        if cmd == "poetry run python runner.py":
            return (False, "", "ImportError: module not found")
        return (True, "", "")

    mocker.patch.object(test, "command", mock_command)
    mocker.patch(
        "src.providers.docker_test.plugin_test.get_plugin_list", return_value={}
    )

    result = await test.run()

    assert "加载出错" in result["output"]
    assert result["load"] is False


async def test_plugin_test_show_dependencies_failed(
    mocker: MockerFixture, tmp_path: Path
):
    """测试获取依赖失败的情况"""
    from src.providers.docker_test.plugin_test import PluginTest

    test = PluginTest("3.12", "project_link", "module_name")

    test_dir = tmp_path / "plugin_test"
    test_dir.mkdir()
    mocker.patch.object(test, "_test_dir", test_dir)

    async def mock_command(cmd: str, timeout: int = 300):  # noqa: ASYNC109
        if cmd == "poetry show project_link":
            return (True, "version      : 1.0.0", "")
        if cmd == "poetry export --without-hashes":
            return (False, "", "Error: could not export")
        if cmd == "poetry run python --version":
            return (True, "Python 3.12.5", "")
        if cmd == "poetry run python runner.py":
            return (True, "", "")
        return (True, "", "")

    mocker.patch.object(test, "command", mock_command)
    mocker.patch(
        "src.providers.docker_test.plugin_test.get_plugin_list", return_value={}
    )

    result = await test.run()

    assert "依赖获取失败" in result["output"]


async def test_plugin_test_get_python_version_failed(
    mocker: MockerFixture, tmp_path: Path
):
    """测试获取 Python 版本失败的情况"""
    from src.providers.docker_test.plugin_test import PluginTest

    test = PluginTest("3.12", "project_link", "module_name")

    test_dir = tmp_path / "plugin_test"
    test_dir.mkdir()
    mocker.patch.object(test, "_test_dir", test_dir)

    async def mock_command(cmd: str, timeout: int = 300):  # noqa: ASYNC109
        if cmd == "poetry show project_link":
            return (True, "version      : 1.0.0", "")
        if cmd == "poetry export --without-hashes":
            return (True, "nonebot2==2.4.0 ; python_version >= '3.9'", "")
        if cmd == "poetry run python --version":
            return (False, "", "Python not found")
        if cmd == "poetry run python runner.py":
            return (True, "", "")
        return (True, "", "")

    mocker.patch.object(test, "command", mock_command)
    mocker.patch(
        "src.providers.docker_test.plugin_test.get_plugin_list", return_value={}
    )

    result = await test.run()

    assert "Python 版本获取失败" in result["output"]
    # 版本应该是 unknown
    assert "python==unknown" in result["test_env"]


async def test_plugin_test_metadata_read_json_decode_error(
    mocker: MockerFixture, tmp_path: Path
):
    """测试 metadata.json 格式不正确的情况"""
    from src.providers.docker_test.plugin_test import PluginTest

    test = PluginTest("3.12", "project_link", "module_name")

    test_dir = tmp_path / "plugin_test"
    test_dir.mkdir()
    mocker.patch.object(test, "_test_dir", test_dir)

    async def mock_command(cmd: str, timeout: int = 300):  # noqa: ASYNC109
        if cmd == "poetry show project_link":
            return (True, "version      : 1.0.0", "")
        if cmd == "poetry export --without-hashes":
            return (True, "nonebot2==2.4.0 ; python_version >= '3.9'", "")
        if cmd == "poetry run python --version":
            return (True, "Python 3.12.5", "")
        if cmd == "poetry run python runner.py":
            # 写入格式不正确的 metadata.json
            with open(test_dir / "metadata.json", "w") as f:
                f.write("invalid json {")
            return (True, "", "")
        return (True, "", "")

    mocker.patch.object(test, "command", mock_command)
    mocker.patch(
        "src.providers.docker_test.plugin_test.get_plugin_list", return_value={}
    )

    result = await test.run()

    assert "metadata.json 格式不正确" in result["output"]
    assert result["metadata"] is None


async def test_plugin_test_metadata_read_exception(
    mocker: MockerFixture, tmp_path: Path
):
    """测试 metadata.json 读取时发生其他异常的情况"""
    from src.providers.docker_test.plugin_test import PluginTest

    test = PluginTest("3.12", "project_link", "module_name")

    test_dir = tmp_path / "plugin_test"
    test_dir.mkdir()
    mocker.patch.object(test, "_test_dir", test_dir)

    async def mock_command(cmd: str, timeout: int = 300):  # noqa: ASYNC109
        if cmd == "poetry show project_link":
            return (True, "version      : 1.0.0", "")
        if cmd == "poetry export --without-hashes":
            return (True, "nonebot2==2.4.0 ; python_version >= '3.9'", "")
        if cmd == "poetry run python --version":
            return (True, "Python 3.12.5", "")
        if cmd == "poetry run python runner.py":
            # 创建 metadata.json，但模拟读取时出错
            metadata_path = test_dir / "metadata.json"
            metadata_path.write_text('{"name": "test"}')
            return (True, "", "")
        return (True, "", "")

    mocker.patch.object(test, "command", mock_command)
    mocker.patch(
        "src.providers.docker_test.plugin_test.get_plugin_list", return_value={}
    )

    # Mock Path.read_text 使其抛出 OSError
    original_read_text = Path.read_text

    def mock_read_text(self, *args, **kwargs):
        if "metadata.json" in str(self):
            raise OSError("Permission denied")
        return original_read_text(self, *args, **kwargs)

    mocker.patch.object(Path, "read_text", mock_read_text)

    result = await test.run()

    assert "插件元数据读取失败" in result["output"]
    assert result["metadata"] is None


async def test_plugin_test_get_deps_with_plugin_dependencies(
    mocker: MockerFixture, tmp_path: Path
):
    """测试获取依赖时包含其他插件的情况"""
    from src.providers.docker_test.plugin_test import PluginTest

    test = PluginTest("3.12", "project-link", "module_name")

    test_dir = tmp_path / "plugin_test"
    test_dir.mkdir()
    mocker.patch.object(test, "_test_dir", test_dir)

    async def mock_command(cmd: str, timeout: int = 300):  # noqa: ASYNC109
        if cmd == "poetry show project-link":
            return (True, "version      : 1.0.0", "")
        if cmd == "poetry export --without-hashes":
            return (
                True,
                """
nonebot2==2.4.0 ; python_version >= '3.9'
pydantic==2.10.0 ; python_version >= '3.9'
nonebot-plugin-dep==1.0.0 ; python_version >= '3.9'
project-link==1.0.0 ; python_version >= '3.9'
""",
                "",
            )
        if cmd == "poetry run python --version":
            return (True, "Python 3.12.5", "")
        if cmd == "poetry run python runner.py":
            return (True, "", "")
        return (True, "", "")

    mocker.patch.object(test, "command", mock_command)
    # 模拟插件列表中包含 nonebot-plugin-dep
    mocker.patch(
        "src.providers.docker_test.plugin_test.get_plugin_list",
        return_value={
            "nonebot-plugin-dep": "nonebot_plugin_dep",
            "project-link": "module_name",  # 自己不应该被包含
        },
    )

    result = await test.run()

    # 验证依赖中包含 nonebot_plugin_dep，但不包含自己
    assert "nonebot_plugin_dep" in result["output"]


def test_strip_ansi():
    """测试 strip_ansi 函数"""
    from src.providers.docker_test.plugin_test import strip_ansi

    # 测试普通字符串
    assert strip_ansi("Hello World") == "Hello World"

    # 测试带 ANSI 转义序列的字符串
    assert strip_ansi("\x1b[31mRed\x1b[0m") == "Red"

    # 测试 None
    assert strip_ansi(None) == ""

    # 测试空字符串
    assert strip_ansi("") == ""


def test_canonicalize_name():
    """测试 canonicalize_name 函数"""
    from src.providers.docker_test.plugin_test import canonicalize_name

    assert canonicalize_name("NoneBot-Plugin-Test") == "nonebot-plugin-test"
    assert canonicalize_name("nonebot_plugin_test") == "nonebot-plugin-test"
    assert canonicalize_name("nonebot.plugin.test") == "nonebot-plugin-test"


async def test_get_plugin_list(mocker: MockerFixture):
    """测试 get_plugin_list 函数"""
    from src.providers.docker_test.plugin_test import get_plugin_list

    mock_response = mocker.MagicMock()
    mock_response.json.return_value = [
        {"project_link": "nonebot-plugin-test", "module_name": "nonebot_plugin_test"},
        {
            "project_link": "nonebot-plugin-example",
            "module_name": "nonebot_plugin_example",
        },
    ]

    mock_get = mocker.patch("httpx.get", return_value=mock_response)

    result = get_plugin_list()

    assert result == {
        "nonebot-plugin-test": "nonebot_plugin_test",
        "nonebot-plugin-example": "nonebot_plugin_example",
    }

    mock_get.assert_called_once()
