import json
from pathlib import Path

from inline_snapshot import snapshot
from pytest_mock import MockerFixture
from respx import MockRouter


def mock_docker_result(path: Path, mocker: MockerFixture):
    from src.providers.docker_test import DockerTestResult

    mock_plugin_test = mocker.MagicMock()

    mocker.patch(
        "src.providers.store_test.validation.DockerPluginTest",
        return_value=mock_plugin_test,
    )

    mock_run = mocker.AsyncMock()
    mock_run.return_value = DockerTestResult(**json.loads(path.read_text()))
    mock_plugin_test.run = mock_run
    return mock_plugin_test


async def test_validate_plugin(
    mocked_api: MockRouter, mocker: MockerFixture, mock_datetime
) -> None:
    """验证插件信息"""
    from src.providers.models import RegistryPlugin, StorePlugin, StoreTestResult
    from src.providers.store_test.validation import validate_plugin

    output_path = Path(__file__).parent / "output.json"
    mock_docker_result(output_path, mocker)

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author_id=1,
        tags=[],
        is_official=True,
    )

    result, new_plugin = await validate_plugin(plugin, "")

    assert result == snapshot(
        StoreTestResult(
            outputs={
                "validation": None,
                "load": """\
创建测试目录 plugin_test
      require("nonebot_plugin_alconna")\
""",
                "metadata": {
                    "name": "TREEHELP",
                    "description": "订阅牛客/CF/AT平台的比赛信息",
                    "usage": """\
/contest.list 获取所有/CF/牛客/AT平台的比赛信息
/contest.subscribe 订阅CF/牛客/AT平台的比赛信息
/contest.update 手动更新比赛信息
""",
                    "type": "application",
                    "homepage": "https://nonebot.dev/",
                    "supported_adapters": None,
                },
            },
            results={"validation": True, "load": True, "metadata": True},
            test_env={"python==3.12.7": True},
            version="0.2.0",
        )
    )
    assert new_plugin == snapshot(
        RegistryPlugin(
            author="he0119",
            desc="订阅牛客/CF/AT平台的比赛信息",
            homepage="https://nonebot.dev/",
            is_official=True,
            module_name="module_name",
            name="TREEHELP",
            project_link="project_link",
            skip_test=False,
            tags=[],
            time="2023-09-01T00:00:00.000000Z",
            type="application",
            valid=True,
            version="0.2.0",
        )
    )

    assert mocked_api["homepage"].called


async def test_validate_plugin_with_previous(
    mocked_api: MockRouter, mocker: MockerFixture, mock_datetime
) -> None:
    """插件验证通过，但提供了之前插件信息的情况

    需要能够正常更新 author_id, tags 和 is_official 等信息
    """
    from src.providers.models import Color, RegistryPlugin, StoreTestResult, Tag
    from src.providers.store_test.validation import StorePlugin, validate_plugin

    output_path = Path(__file__).parent / "output.json"
    mock_docker_result(output_path, mocker)

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author_id=1,
        tags=[Tag(label="test", color=Color("ffffff"))],
        is_official=True,
    )

    result, new_plugin = await validate_plugin(
        plugin,
        "",
        RegistryPlugin(
            module_name="module_name",
            project_link="project_link",
            name="name",
            author="author",
            desc="desc",
            homepage="https://nonebot.dev/",
            tags=[],
            is_official=False,
            type="application",
            supported_adapters=None,
            valid=True,
            time="2023-06-22 12:10:18",
            version="0.2.0",
            skip_test=False,
        ),
    )

    assert result == snapshot(
        StoreTestResult(
            outputs={
                "validation": None,
                "load": """\
创建测试目录 plugin_test
      require("nonebot_plugin_alconna")\
""",
                "metadata": {
                    "name": "TREEHELP",
                    "description": "订阅牛客/CF/AT平台的比赛信息",
                    "usage": """\
/contest.list 获取所有/CF/牛客/AT平台的比赛信息
/contest.subscribe 订阅CF/牛客/AT平台的比赛信息
/contest.update 手动更新比赛信息
""",
                    "type": "application",
                    "homepage": "https://nonebot.dev/",
                    "supported_adapters": None,
                },
            },
            results={"validation": True, "load": True, "metadata": True},
            test_env={"python==3.12.7": True},
            version="0.2.0",
        )
    )

    assert new_plugin.model_dump() == snapshot(
        {
            "module_name": "module_name",
            "project_link": "project_link",
            "name": "TREEHELP",
            "desc": "订阅牛客/CF/AT平台的比赛信息",
            "author": "he0119",
            "homepage": "https://nonebot.dev/",
            "tags": [{"label": "test", "color": "#ffffff"}],
            "is_official": True,
            "type": "application",
            "supported_adapters": None,
            "valid": True,
            "time": "2023-09-01T00:00:00.000000Z",
            "version": "0.2.0",
            "skip_test": False,
        }
    )

    assert mocked_api["homepage"].called


async def test_validate_plugin_skip_test(
    mocked_api: MockRouter, mocker: MockerFixture, mock_datetime
) -> None:
    """跳过插件测试的情况

    如果插件之前是跳过测试的，如果插件测试成功，应将 skip_test 设置为 False。
    """
    from src.providers.models import RegistryPlugin, StoreTestResult
    from src.providers.store_test.validation import StorePlugin, validate_plugin

    output_path = Path(__file__).parent / "output.json"
    mock_docker_result(output_path, mocker)

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author_id=1,
        tags=[],
        is_official=False,
    )

    result, new_plugin = await validate_plugin(plugin, "")

    assert result == snapshot(
        StoreTestResult(
            outputs={
                "validation": None,
                "load": """\
创建测试目录 plugin_test
      require("nonebot_plugin_alconna")\
""",
                "metadata": {
                    "name": "TREEHELP",
                    "description": "订阅牛客/CF/AT平台的比赛信息",
                    "usage": """\
/contest.list 获取所有/CF/牛客/AT平台的比赛信息
/contest.subscribe 订阅CF/牛客/AT平台的比赛信息
/contest.update 手动更新比赛信息
""",
                    "type": "application",
                    "homepage": "https://nonebot.dev/",
                    "supported_adapters": None,
                },
            },
            results={"validation": True, "load": True, "metadata": True},
            test_env={"python==3.12.7": True},
            version="0.2.0",
        )
    )
    assert new_plugin == snapshot(
        RegistryPlugin(
            author="he0119",
            desc="订阅牛客/CF/AT平台的比赛信息",
            homepage="https://nonebot.dev/",
            is_official=False,
            module_name="module_name",
            name="TREEHELP",
            project_link="project_link",
            skip_test=False,
            tags=[],
            time="2023-09-01T00:00:00.000000Z",
            type="application",
            valid=True,
            version="0.2.0",
        )
    )

    assert mocked_api["homepage"].called


async def test_validate_plugin_skip_test_plugin_test_failed(
    mocked_api: MockRouter, mocker: MockerFixture, mock_datetime
) -> None:
    """跳过插件测试的情况

    如果插件之前是跳过测试的，如果插件测试失败，应不改变 skip_test 的值。
    """
    from src.providers.models import RegistryPlugin, StoreTestResult
    from src.providers.store_test.validation import StorePlugin, validate_plugin

    output_path = Path(__file__).parent / "output_failed.json"
    mock_docker_result(output_path, mocker)

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author_id=1,
        tags=[],
        is_official=False,
    )

    result, new_plugin = await validate_plugin(
        plugin,
        "",
        previous_plugin=RegistryPlugin(
            module_name="nonebot_plugin_treehelp",
            project_link="nonebot-plugin-treehelp",
            name="帮助",
            desc="获取插件帮助信息",
            author="he0119",
            homepage="https://nonebot.dev/",
            tags=[],
            is_official=False,
            type="application",
            supported_adapters=None,
            valid=True,
            time="2023-06-22 12:10:18",
            version="0.3.0",
            skip_test=True,
        ),
    )

    assert result == snapshot(
        StoreTestResult(
            outputs={
                "validation": {
                    "data": {
                        "module_name": "nonebot_plugin_treehelp",
                        "project_link": "nonebot-plugin-treehelp",
                        "time": "2024-07-13T04:41:40.905441Z",
                        "version": "0.3.9",
                        "name": "帮助",
                        "desc": "获取插件帮助信息",
                        "author": "he0119",
                        "author_id": 1,
                        "homepage": "https://nonebot.dev/",
                        "tags": [],
                        "is_official": False,
                        "type": "application",
                        "supported_adapters": None,
                        "load": True,
                        "skip_test": True,
                        "test_output": """\
创建测试目录 plugin_test
        For further information visit https://errors.pydantic.dev/2.9/v/model_type\x1b[0m\
""",
                    },
                    "errors": [
                        {
                            "type": "plugin.metadata",
                            "loc": ("metadata",),
                            "msg": "无法获取到插件元数据",
                            "input": False,
                            "ctx": {"load": None},
                        }
                    ],
                },
                "load": """\
创建测试目录 plugin_test
        For further information visit https://errors.pydantic.dev/2.9/v/model_type\x1b[0m\
""",
                "metadata": None,
            },
            results={"validation": False, "load": False, "metadata": False},
            test_env={"python==3.12.7": True},
            version="0.3.9",
        )
    )
    assert new_plugin == snapshot(
        RegistryPlugin(
            author="he0119",
            desc="获取插件帮助信息",
            homepage="https://nonebot.dev/",
            is_official=False,
            module_name="nonebot_plugin_treehelp",
            name="帮助",
            project_link="nonebot-plugin-treehelp",
            skip_test=True,
            tags=[],
            time="2024-07-13T04:41:40.905441Z",
            type="application",
            valid=False,
            version="0.3.9",
        )
    )

    assert mocked_api["homepage"].called


async def test_validate_plugin_failed_with_previous(
    mocked_api: MockRouter, mocker: MockerFixture, mock_datetime
) -> None:
    """插件验证失败，但提供了之前插件信息的情况

    需要能够正常更新 author_id, tags 和 is_official 等信息
    """
    from src.providers.models import RegistryPlugin, StoreTestResult
    from src.providers.store_test.validation import StorePlugin, validate_plugin

    output_path = Path(__file__).parent / "output_failed.json"
    mock_docker_result(output_path, mocker)

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author_id=1,
        tags=[],
        is_official=True,
    )

    result, new_plugin = await validate_plugin(
        plugin,
        "",
        RegistryPlugin(
            module_name="module_name",
            project_link="project_link",
            name="name",
            author="author",
            desc="desc",
            homepage="https://nonebot.dev/",
            tags=[],
            is_official=False,
            type="application",
            supported_adapters=None,
            valid=True,
            time="2023-06-22 12:10:18",
            version="0.2.0",
            skip_test=False,
        ),
    )

    assert result == snapshot(
        StoreTestResult(
            outputs={
                "validation": {
                    "data": {
                        "module_name": "module_name",
                        "project_link": "project_link",
                        "time": "2023-09-01T00:00:00.000000Z",
                        "name": "name",
                        "desc": "desc",
                        "author": "he0119",
                        "author_id": 1,
                        "homepage": "https://nonebot.dev/",
                        "tags": [],
                        "is_official": True,
                        "type": "application",
                        "supported_adapters": None,
                        "skip_test": False,
                        "version": "0.3.9",
                        "test_output": """\
创建测试目录 plugin_test
        For further information visit https://errors.pydantic.dev/2.9/v/model_type\x1b[0m\
""",
                    },
                    "errors": [
                        {
                            "type": "plugin.test",
                            "loc": ("load",),
                            "msg": "插件无法正常加载",
                            "input": False,
                            "ctx": {
                                "output": """\
创建测试目录 plugin_test
        For further information visit https://errors.pydantic.dev/2.9/v/model_type\x1b[0m\
"""
                            },
                        },
                        {
                            "type": "plugin.metadata",
                            "loc": ("metadata",),
                            "msg": "无法获取到插件元数据",
                            "input": False,
                            "ctx": {"load": None},
                        },
                    ],
                },
                "load": """\
创建测试目录 plugin_test
        For further information visit https://errors.pydantic.dev/2.9/v/model_type\x1b[0m\
""",
                "metadata": None,
            },
            results={"validation": False, "load": False, "metadata": False},
            test_env={"python==3.12.7": True},
            version="0.3.9",
        )
    )

    assert new_plugin == snapshot(
        RegistryPlugin(
            author="he0119",
            desc="desc",
            homepage="https://nonebot.dev/",
            is_official=True,
            module_name="module_name",
            name="name",
            project_link="project_link",
            skip_test=False,
            tags=[],
            time="2023-09-01T00:00:00.000000Z",
            type="application",
            valid=False,
            version="0.3.9",
        )
    )

    assert mocked_api["homepage"].called
