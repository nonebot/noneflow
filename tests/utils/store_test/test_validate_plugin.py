import json
from datetime import datetime
from pathlib import Path

from inline_snapshot import snapshot
from pytest_mock import MockerFixture
from respx import MockRouter
from zoneinfo import ZoneInfo


def mock_docker_result(path: Path, mocker: MockerFixture):
    from src.providers.store_test.models import DockerTestResult

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
    tmp_path: Path, mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """验证插件信息"""
    from src.providers.store_test.validation import StorePlugin, validate_plugin
    from src.providers.store_test.models import (
        TestResult,
        Metadata,
        Plugin,
    )

    mock_datetime = mocker.patch("src.providers.store_test.models.datetime")
    mock_datetime.now.return_value = datetime(
        2023, 8, 23, 9, 22, 14, 836035, tzinfo=ZoneInfo("Asia/Shanghai")
    )

    output_path = Path(__file__).parent / "output.json"
    mock_docker_result(output_path, mocker)

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author_id=1,
        tags=[],
        is_official=True,
    )

    result, new_plugin = await validate_plugin(plugin, "", False)

    assert result == snapshot(
        TestResult(
            config="",
            outputs={
                "validation": None,
                "load": [
                    "创建测试目录 plugin_test",
                    "项目 nonebot-plugin_acm_reminder 创建成功。",
                    "    \x1b[39;1mVirtualenv\x1b[39;22m",
                    "    \x1b[34mPython\x1b[39m:         \x1b[32m3.11.10\x1b[39m",
                    "    \x1b[34mImplementation\x1b[39m: \x1b[32mCPython\x1b[39m",
                    "    \x1b[34mPath\x1b[39m:           \x1b[32mNA\x1b[39m",
                    "    \x1b[34mExecutable\x1b[39m:     \x1b[32mNA\x1b[39m",
                    "    ",
                    "    \x1b[39;1mBase\x1b[39;22m",
                    "    \x1b[34mPlatform\x1b[39m:   \x1b[32mlinux\x1b[39m",
                    "    \x1b[34mOS\x1b[39m:         \x1b[32mposix\x1b[39m",
                    "    \x1b[34mPython\x1b[39m:     \x1b[32m3.11.10\x1b[39m",
                    "    \x1b[34mPath\x1b[39m:       \x1b[32m/usr/local\x1b[39m",
                    "    \x1b[34mExecutable\x1b[39m: \x1b[32m/usr/local/bin/python3.11\x1b[39m",
                    "    Using version ^0.2.0 for nonebot-plugin-acm-reminder",
                    "    ",
                    "    Updating dependencies",
                    "    Resolving dependencies...",
                    "    ",
                    "    Package operations: 46 installs, 0 updates, 0 removals",
                    "    ",
                    "      - Installing typing-extensions (4.12.2)",
                    "      - Installing annotated-types (0.7.0)",
                    "      - Installing idna (3.10)",
                    "      - Installing multidict (6.1.0)",
                    "      - Installing propcache (0.2.0)",
                    "      - Installing pydantic-core (2.23.4)",
                    "      - Installing tarina (0.5.8)",
                    "      - Installing loguru (0.7.2)",
                    "      - Installing nepattern (0.7.6)",
                    "      - Installing pydantic (2.9.2)",
                    "      - Installing pygtrie (2.5.0)",
                    "      - Installing python-dotenv (1.0.1)",
                    "      - Installing yarl (1.14.0)",
                    "      - Installing arclet-alconna (1.8.30)",
                    "      - Installing certifi (2024.8.30)",
                    "      - Installing greenlet (3.0.3)",
                    "      - Installing h11 (0.14.0)",
                    "      - Installing markdown (3.7)",
                    "      - Installing markupsafe (3.0.1)",
                    "      - Installing nonebot2 (2.3.3)",
                    "      - Installing pyee (12.0.0)",
                    "      - Installing pytz (2024.2)",
                    "      - Installing pyyaml (6.0.2)",
                    "      - Installing six (1.16.0)",
                    "      - Installing sniffio (1.3.1)",
                    "      - Installing tzlocal (5.2)",
                    "      - Installing zipp (3.20.2)",
                    "      - Installing aiofiles (24.1.0)",
                    "      - Installing anyio (4.6.0)",
                    "      - Installing apscheduler (3.10.4)",
                    "      - Installing arclet-alconna-tools (0.7.9)",
                    "      - Installing httpcore (1.0.6)",
                    "      - Installing importlib-metadata (8.5.0)",
                    "      - Installing jinja2 (3.1.4)",
                    "      - Installing nonebot-plugin-waiter (0.8.0)",
                    "      - Installing playwright (1.47.0)",
                    "      - Installing pygments (2.18.0)",
                    "      - Installing pymdown-extensions (10.11.2)",
                    "      - Installing python-markdown-math (0.8)",
                    "      - Installing soupsieve (2.6)",
                    "      - Installing beautifulsoup4 (4.12.3)",
                    "      - Installing httpx (0.27.2)",
                    "      - Installing nonebot-plugin-alconna (0.53.0)",
                    "      - Installing nonebot-plugin-apscheduler (0.5.0)",
                    "      - Installing nonebot-plugin-htmlrender (0.3.5)",
                    "      - Installing nonebot-plugin-acm-reminder (0.2.0)",
                    "    ",
                    "    Writing lock file",
                    "插件 nonebot-plugin_acm_reminder 依赖的插件如下：",
                    "    nonebot_plugin_acm_reminder, nonebot_plugin_alconna, nonebot_plugin_apscheduler, nonebot_plugin_htmlrender, nonebot_plugin_waiter",
                    "插件 nonebot-plugin_acm_reminder 的信息如下：",
                    "    name         : nonebot-plugin-acm-reminder                                              ",
                    "     version      : 0.2.0                                                                    ",
                    "     description  : A subscribe CodeForces/NowCoder/Atcoder contest info plugin for nonebot2 ",
                    "    ",
                    "    dependencies",
                    "     - BeautifulSoup4 >=4.12.3",
                    "     - httpx >=0.23.3",
                    "     - nonebot-plugin-alconna >=0.42.0",
                    "     - nonebot-plugin-apscheduler >=0.2.0",
                    "     - nonebot-plugin-htmlrender >=0.2.0.3",
                    "     - nonebot2 >=2.2.1",
                    "     - pydantic >=2.6.4",
                    "插件 nonebot_plugin_acm_reminder 加载正常：",
                    "    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | NoneBot is initializing...",
                    "    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[1mINFO\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Current \x1b[33m\x1b[1mEnv: prod\x1b[0m\x1b[33m\x1b[0m",
                    '    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_apscheduler\x1b[0m"',
                    '    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_htmlrender\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_alconna:uniseg\x1b[0m" from "\x1b[35mnonebot_plugin_alconna.uniseg\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_alconna\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_acm_reminder\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_waiter\x1b[0m"',
                    "    /tmp/plugin_test/nonebot-plugin_acm_reminder-nonebot_plugin_acm_reminder/.venv/lib/python3.11/site-packages/nonebot_plugin_acm_reminder/__init__.py:13: RuntimeWarning: No adapters found, please make sure you have installed at least one adapter.",
                    '      require("nonebot_plugin_alconna")',
                ],
                "metadata": Metadata(
                    desc="订阅牛客/CF/AT平台的比赛信息",
                    homepage="https://nonebot.dev/",
                    name="TREEHELP",
                    supported_adapters=None,
                    type="application",
                ),
            },
            results={"validation": True, "load": True, "metadata": True},
            test_env={"unknown": True},
            version="0.2.0",
        )
    )
    assert new_plugin == snapshot(
        Plugin(
            author="he0119",
            author_id=1,
            desc="订阅牛客/CF/AT平台的比赛信息",
            homepage="https://nonebot.dev/",
            is_official=True,
            module_name="module_name",
            name="TREEHELP",
            project_link="project_link",
            skip_test=False,
            supported_adapters=None,
            tags=[],
            time="2023-09-01T00:00:00+00:00Z",
            type="application",
            valid=True,
            version="0.2.0",
        )
    )

    assert mocked_api["homepage"].called


async def test_validate_plugin_with_data(
    mocked_api: MockRouter,
    mocker: MockerFixture,
) -> None:
    """验证插件信息，提供数据的情况

    应该不会调用 API，直接使用传递进来的数据，并且 metadata 会缺少 usage（因为拉取请求关闭时无法获取，所以并没有传递过来）。
    """
    from src.providers.store_test.validation import StorePlugin, validate_plugin
    from src.providers.store_test.models import (
        TestResult,
        Metadata,
        Plugin,
    )

    mock_datetime = mocker.patch("src.providers.store_test.models.datetime")
    mock_datetime.now.return_value = datetime(
        2023, 8, 23, 9, 22, 14, 836035, tzinfo=ZoneInfo("Asia/Shanghai")
    )

    mocked_plugin_test = mocker.patch(
        "src.providers.store_test.validation.DockerPluginTest"
    )

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author_id=1,
        tags=[],
        is_official=False,
    )

    data = {
        "project_link": "project_link",
        "module_name": "module_name",
        "author": "author",
        "name": "帮助",
        "desc": "获取插件帮助信息",
        "homepage": "https://nonebot.dev/",
        "author_id": 1,
        "is_official": False,
        "tags": [],
        "type": "application",
        "supported_adapters": None,
    }

    result, new_plugin = await validate_plugin(plugin, "", False, json.dumps(data))

    assert result == snapshot(
        TestResult(
            config="",
            outputs={
                "validation": None,
                "load": "已跳过测试",
                "metadata": Metadata(
                    desc="获取插件帮助信息",
                    homepage="https://nonebot.dev/",
                    name="帮助",
                    supported_adapters=None,
                    type="application",
                ),
            },
            results={"validation": True, "load": True, "metadata": True},
            test_env={"skip_test": True},
            version=None,
        )
    )
    assert new_plugin == snapshot(
        Plugin(
            author="author",
            author_id=1,
            desc="获取插件帮助信息",
            homepage="https://nonebot.dev/",
            is_official=False,
            module_name="module_name",
            name="帮助",
            project_link="project_link",
            skip_test=True,
            supported_adapters=None,
            tags=[],
            time="2023-09-01T00:00:00+00:00Z",
            type="application",
            valid=True,
            version="0.0.1",
        )
    )

    assert not mocked_api["homepage"].called

    mocked_plugin_test.assert_not_called()


async def test_validate_plugin_skip_test(
    tmp_path: Path, mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """跳过插件测试的情况

    如果插件之前是跳过测试的，如果插件测试成功，应将 skip_test 设置为 False。
    """
    from src.providers.store_test.validation import StorePlugin, validate_plugin
    from src.providers.store_test.models import (
        TestResult,
        Metadata,
        Plugin,
    )

    mock_datetime = mocker.patch("src.providers.store_test.models.datetime")
    mock_datetime.now.return_value = datetime(
        2023, 8, 23, 9, 22, 14, 836035, tzinfo=ZoneInfo("Asia/Shanghai")
    )

    output_path = Path(__file__).parent / "output.json"
    mock_plugin_test = mock_docker_result(output_path, mocker)
    mocker.patch(
        "src.providers.store_test.validation.DockerPluginTest",
        return_value=mock_plugin_test,
    )

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author_id=1,
        tags=[],
        is_official=False,
    )

    result, new_plugin = await validate_plugin(plugin, "", True)

    assert result == snapshot(
        TestResult(
            config="",
            outputs={
                "validation": None,
                "load": [
                    "创建测试目录 plugin_test",
                    "项目 nonebot-plugin_acm_reminder 创建成功。",
                    "    \x1b[39;1mVirtualenv\x1b[39;22m",
                    "    \x1b[34mPython\x1b[39m:         \x1b[32m3.11.10\x1b[39m",
                    "    \x1b[34mImplementation\x1b[39m: \x1b[32mCPython\x1b[39m",
                    "    \x1b[34mPath\x1b[39m:           \x1b[32mNA\x1b[39m",
                    "    \x1b[34mExecutable\x1b[39m:     \x1b[32mNA\x1b[39m",
                    "    ",
                    "    \x1b[39;1mBase\x1b[39;22m",
                    "    \x1b[34mPlatform\x1b[39m:   \x1b[32mlinux\x1b[39m",
                    "    \x1b[34mOS\x1b[39m:         \x1b[32mposix\x1b[39m",
                    "    \x1b[34mPython\x1b[39m:     \x1b[32m3.11.10\x1b[39m",
                    "    \x1b[34mPath\x1b[39m:       \x1b[32m/usr/local\x1b[39m",
                    "    \x1b[34mExecutable\x1b[39m: \x1b[32m/usr/local/bin/python3.11\x1b[39m",
                    "    Using version ^0.2.0 for nonebot-plugin-acm-reminder",
                    "    ",
                    "    Updating dependencies",
                    "    Resolving dependencies...",
                    "    ",
                    "    Package operations: 46 installs, 0 updates, 0 removals",
                    "    ",
                    "      - Installing typing-extensions (4.12.2)",
                    "      - Installing annotated-types (0.7.0)",
                    "      - Installing idna (3.10)",
                    "      - Installing multidict (6.1.0)",
                    "      - Installing propcache (0.2.0)",
                    "      - Installing pydantic-core (2.23.4)",
                    "      - Installing tarina (0.5.8)",
                    "      - Installing loguru (0.7.2)",
                    "      - Installing nepattern (0.7.6)",
                    "      - Installing pydantic (2.9.2)",
                    "      - Installing pygtrie (2.5.0)",
                    "      - Installing python-dotenv (1.0.1)",
                    "      - Installing yarl (1.14.0)",
                    "      - Installing arclet-alconna (1.8.30)",
                    "      - Installing certifi (2024.8.30)",
                    "      - Installing greenlet (3.0.3)",
                    "      - Installing h11 (0.14.0)",
                    "      - Installing markdown (3.7)",
                    "      - Installing markupsafe (3.0.1)",
                    "      - Installing nonebot2 (2.3.3)",
                    "      - Installing pyee (12.0.0)",
                    "      - Installing pytz (2024.2)",
                    "      - Installing pyyaml (6.0.2)",
                    "      - Installing six (1.16.0)",
                    "      - Installing sniffio (1.3.1)",
                    "      - Installing tzlocal (5.2)",
                    "      - Installing zipp (3.20.2)",
                    "      - Installing aiofiles (24.1.0)",
                    "      - Installing anyio (4.6.0)",
                    "      - Installing apscheduler (3.10.4)",
                    "      - Installing arclet-alconna-tools (0.7.9)",
                    "      - Installing httpcore (1.0.6)",
                    "      - Installing importlib-metadata (8.5.0)",
                    "      - Installing jinja2 (3.1.4)",
                    "      - Installing nonebot-plugin-waiter (0.8.0)",
                    "      - Installing playwright (1.47.0)",
                    "      - Installing pygments (2.18.0)",
                    "      - Installing pymdown-extensions (10.11.2)",
                    "      - Installing python-markdown-math (0.8)",
                    "      - Installing soupsieve (2.6)",
                    "      - Installing beautifulsoup4 (4.12.3)",
                    "      - Installing httpx (0.27.2)",
                    "      - Installing nonebot-plugin-alconna (0.53.0)",
                    "      - Installing nonebot-plugin-apscheduler (0.5.0)",
                    "      - Installing nonebot-plugin-htmlrender (0.3.5)",
                    "      - Installing nonebot-plugin-acm-reminder (0.2.0)",
                    "    ",
                    "    Writing lock file",
                    "插件 nonebot-plugin_acm_reminder 依赖的插件如下：",
                    "    nonebot_plugin_acm_reminder, nonebot_plugin_alconna, nonebot_plugin_apscheduler, nonebot_plugin_htmlrender, nonebot_plugin_waiter",
                    "插件 nonebot-plugin_acm_reminder 的信息如下：",
                    "    name         : nonebot-plugin-acm-reminder                                              ",
                    "     version      : 0.2.0                                                                    ",
                    "     description  : A subscribe CodeForces/NowCoder/Atcoder contest info plugin for nonebot2 ",
                    "    ",
                    "    dependencies",
                    "     - BeautifulSoup4 >=4.12.3",
                    "     - httpx >=0.23.3",
                    "     - nonebot-plugin-alconna >=0.42.0",
                    "     - nonebot-plugin-apscheduler >=0.2.0",
                    "     - nonebot-plugin-htmlrender >=0.2.0.3",
                    "     - nonebot2 >=2.2.1",
                    "     - pydantic >=2.6.4",
                    "插件 nonebot_plugin_acm_reminder 加载正常：",
                    "    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | NoneBot is initializing...",
                    "    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[1mINFO\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Current \x1b[33m\x1b[1mEnv: prod\x1b[0m\x1b[33m\x1b[0m",
                    '    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_apscheduler\x1b[0m"',
                    '    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_htmlrender\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_alconna:uniseg\x1b[0m" from "\x1b[35mnonebot_plugin_alconna.uniseg\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_alconna\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_acm_reminder\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_waiter\x1b[0m"',
                    "    /tmp/plugin_test/nonebot-plugin_acm_reminder-nonebot_plugin_acm_reminder/.venv/lib/python3.11/site-packages/nonebot_plugin_acm_reminder/__init__.py:13: RuntimeWarning: No adapters found, please make sure you have installed at least one adapter.",
                    '      require("nonebot_plugin_alconna")',
                ],
                "metadata": Metadata(
                    desc="订阅牛客/CF/AT平台的比赛信息",
                    homepage="https://nonebot.dev/",
                    name="TREEHELP",
                    supported_adapters=None,
                    type="application",
                ),
            },
            results={"validation": True, "load": True, "metadata": True},
            test_env={"unknown": True},
            version="0.2.0",
        )
    )
    assert new_plugin == snapshot(
        Plugin(
            author="he0119",
            author_id=1,
            desc="订阅牛客/CF/AT平台的比赛信息",
            homepage="https://nonebot.dev/",
            is_official=False,
            module_name="module_name",
            name="TREEHELP",
            project_link="project_link",
            skip_test=False,
            supported_adapters=None,
            tags=[],
            time="2023-09-01T00:00:00+00:00Z",
            type="application",
            valid=True,
            version="0.2.0",
        )
    )

    assert mocked_api["homepage"].called


async def test_validate_plugin_skip_test_plugin_test_failed(
    tmp_path: Path, mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """跳过插件测试的情况

    如果插件之前是跳过测试的，如果插件测试失败，应不改变 skip_test 的值。
    """
    from src.providers.store_test.validation import StorePlugin, validate_plugin
    from src.providers.store_test.models import (
        TestResult,
        Plugin,
    )

    mock_datetime = mocker.patch("src.providers.store_test.models.datetime")
    mock_datetime.now.return_value = datetime(
        2023, 8, 23, 9, 22, 14, 836035, tzinfo=ZoneInfo("Asia/Shanghai")
    )

    output_path = Path(__file__).parent / "output_failed.json"
    mock_plugin_test = mock_docker_result(output_path, mocker)
    mocker.patch(
        "src.providers.store_test.validation.DockerPluginTest",
        return_value=mock_plugin_test,
    )

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
        True,
        previous_plugin=Plugin(
            module_name="nonebot_plugin_treehelp",
            project_link="nonebot-plugin-treehelp",
            name="帮助",
            desc="获取插件帮助信息",
            author="he0119",
            author_id=1,
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
        TestResult(
            config="",
            outputs={
                "validation": None,
                "load": [
                    "创建测试目录 plugin_test",
                    "项目 nonebot-plugin_orangedice 创建成功。",
                    "    \x1b[39;1mVirtualenv\x1b[39;22m",
                    "    \x1b[34mPython\x1b[39m:         \x1b[32m3.11.10\x1b[39m",
                    "    \x1b[34mImplementation\x1b[39m: \x1b[32mCPython\x1b[39m",
                    "    \x1b[34mPath\x1b[39m:           \x1b[32mNA\x1b[39m",
                    "    \x1b[34mExecutable\x1b[39m:     \x1b[32mNA\x1b[39m",
                    "    ",
                    "    \x1b[39;1mBase\x1b[39;22m",
                    "    \x1b[34mPlatform\x1b[39m:   \x1b[32mlinux\x1b[39m",
                    "    \x1b[34mOS\x1b[39m:         \x1b[32mposix\x1b[39m",
                    "    \x1b[34mPython\x1b[39m:     \x1b[32m3.11.10\x1b[39m",
                    "    \x1b[34mPath\x1b[39m:       \x1b[32m/usr/local\x1b[39m",
                    "    \x1b[34mExecutable\x1b[39m: \x1b[32m/usr/local/bin/python3.11\x1b[39m",
                    "    Using version ^0.3.9 for nonebot-plugin-orangedice",
                    "    ",
                    "    Updating dependencies",
                    "    Resolving dependencies...",
                    "    ",
                    "    Package operations: 18 installs, 0 updates, 0 removals",
                    "    ",
                    "      - Installing typing-extensions (4.12.2)",
                    "      - Installing annotated-types (0.7.0)",
                    "      - Installing idna (3.10)",
                    "      - Installing multidict (6.1.0)",
                    "      - Installing propcache (0.2.0)",
                    "      - Installing pydantic-core (2.23.4)",
                    "      - Installing greenlet (3.1.1)",
                    "      - Installing loguru (0.7.2)",
                    "      - Installing pydantic (2.9.2)",
                    "      - Installing pygtrie (2.5.0)",
                    "      - Installing python-dotenv (1.0.1)",
                    "      - Installing yarl (1.14.0)",
                    "      - Installing msgpack (1.1.0)",
                    "      - Installing nonebot2 (2.3.3)",
                    "      - Installing sqlalchemy (2.0.35)",
                    "      - Installing nonebot-adapter-onebot (2.4.5)",
                    "      - Installing sqlmodel (0.0.22)",
                    "      - Installing nonebot-plugin-orangedice (0.3.9)",
                    "    ",
                    "    Writing lock file",
                    "插件 nonebot-plugin_orangedice 依赖的插件如下：",
                    "    nonebot_plugin_orangedice",
                    "插件 nonebot-plugin_orangedice 的信息如下：",
                    "    name         : nonebot-plugin-orangedice      ",
                    "     version      : 0.3.9                          ",
                    "     description  : A COC dice plugin for nonebot2 ",
                    "    ",
                    "    dependencies",
                    "     - nonebot-adapter-onebot >=2.2.3",
                    "     - nonebot2 >=2.0.1",
                    "     - pydantic >=1.9.2",
                    "     - sqlmodel >=0.0.8",
                    "插件 nonebot_plugin_orangedice 加载出错：",
                    "    \x1b[32m10-10 14:22:11\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | NoneBot is initializing...",
                    "    \x1b[32m10-10 14:22:11\x1b[0m [\x1b[1mINFO\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Current \x1b[33m\x1b[1mEnv: prod\x1b[0m\x1b[33m\x1b[0m",
                    '    \x1b[32m10-10 14:22:12\x1b[0m [\x1b[31m\x1b[1mERROR\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | \x1b[31m\x1b[48;2;248;187;208mFailed to import "nonebot_plugin_orangedice"\x1b[0m\x1b[31m\x1b[0m',
                    "    \x1b[33m\x1b[1mTraceback (most recent call last):\x1b[0m",
                    '      File "\x1b[32m/tmp/plugin_test/nonebot-plugin_orangedice-nonebot_plugin_orangedice/\x1b[0m\x1b[32m\x1b[1mrunner.py\x1b[0m", line \x1b[33m16\x1b[0m, in \x1b[35m<module>\x1b[0m',
                    '        \x1b[1mplugin\x1b[0m \x1b[35m\x1b[1m=\x1b[0m \x1b[1mload_plugin\x1b[0m\x1b[1m(\x1b[0m\x1b[36m"nonebot_plugin_orangedice"\x1b[0m\x1b[1m)\x1b[0m',
                    '      File "/tmp/plugin_test/nonebot-plugin_orangedice-nonebot_plugin_orangedice/.venv/lib/python3.11/site-packages/nonebot/plugin/load.py", line 40, in load_plugin',
                    "        return manager.load_plugin(module_path)",
                    '    > File "/tmp/plugin_test/nonebot-plugin_orangedice-nonebot_plugin_orangedice/.venv/lib/python3.11/site-packages/nonebot/plugin/manager.py", line 167, in load_plugin',
                    "        module = importlib.import_module(self._third_party_plugin_ids[name])",
                    '      File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module',
                    "        return _bootstrap._gcd_import(name[level:], package, level)",
                    '      File "<frozen importlib._bootstrap>", line 1204, in _gcd_import',
                    '      File "<frozen importlib._bootstrap>", line 1176, in _find_and_load',
                    '      File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked',
                    '      File "<frozen importlib._bootstrap>", line 690, in _load_unlocked',
                    '      File "/tmp/plugin_test/nonebot-plugin_orangedice-nonebot_plugin_orangedice/.venv/lib/python3.11/site-packages/nonebot/plugin/manager.py", line 255, in exec_module',
                    "        super().exec_module(module)",
                    '      File "<frozen importlib._bootstrap_external>", line 940, in exec_module',
                    '      File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed',
                    '      File "/tmp/plugin_test/nonebot-plugin_orangedice-nonebot_plugin_orangedice/.venv/lib/python3.11/site-packages/nonebot_plugin_orangedice/__init__.py", line 64, in <module>',
                    "        plugin_config = Config.parse_obj(driver.config)",
                    '      File "/tmp/plugin_test/nonebot-plugin_orangedice-nonebot_plugin_orangedice/.venv/lib/python3.11/site-packages/pydantic/main.py", line 1162, in parse_obj',
                    "        return cls.model_validate(obj)",
                    '      File "/tmp/plugin_test/nonebot-plugin_orangedice-nonebot_plugin_orangedice/.venv/lib/python3.11/site-packages/pydantic/main.py", line 596, in model_validate',
                    "        return cls.__pydantic_validator__.validate_python(",
                    "    \x1b[31m\x1b[1mpydantic_core._pydantic_core.ValidationError\x1b[0m:\x1b[1m 1 validation error for Config",
                    "      Input should be a valid dictionary or instance of Config [type=model_type, input_value=Config(driver='fake', hos....timedelta(seconds=120)), input_type=Config]",
                    "        For further information visit https://errors.pydantic.dev/2.9/v/model_type\x1b[0m",
                ],
                "metadata": None,
            },
            results={"validation": True, "load": False, "metadata": False},
            test_env={"unknown": True},
            version="0.3.9",
        )
    )
    assert new_plugin == snapshot(
        Plugin(
            author="he0119",
            author_id=1,
            desc="获取插件帮助信息",
            homepage="https://nonebot.dev/",
            is_official=False,
            module_name="nonebot_plugin_treehelp",
            name="帮助",
            project_link="nonebot-plugin-treehelp",
            skip_test=True,
            supported_adapters=None,
            tags=[],
            time="2023-09-01T00:00:00+00:00Z",
            type="application",
            valid=True,
            version="0.3.9",
        )
    )

    assert mocked_api["homepage"].called


async def test_validate_plugin_failed(
    tmp_path: Path, mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """插件验证失败的情况"""
    from src.providers.store_test.validation import StorePlugin, validate_plugin
    from src.providers.store_test.models import (
        TestResult,
        Metadata,
    )

    mock_datetime = mocker.patch("src.providers.store_test.models.datetime")
    mock_datetime.now.return_value = datetime(
        2023, 8, 23, 9, 22, 14, 836035, tzinfo=ZoneInfo("Asia/Shanghai")
    )

    output_path = Path(__file__).parent / "output.json"
    mock_plugin_test = mock_docker_result(output_path, mocker)
    mock_plugin_test.run.return_value.load = False
    mocker.patch(
        "src.providers.store_test.validation.DockerPluginTest",
        return_value=mock_plugin_test,
    )

    plugin = StorePlugin(
        module_name="module_name",
        project_link="project_link",
        author_id=1,
        tags=[],
        is_official=False,
    )

    result, new_plugin = await validate_plugin(plugin, "", False)

    assert result == snapshot(
        TestResult(
            config="",
            outputs={
                "validation": {
                    "data": {
                        "module_name": "module_name",
                        "project_link": "project_link",
                        "name": "TREEHELP",
                        "desc": "订阅牛客/CF/AT平台的比赛信息",
                        "author": "he0119",
                        "author_id": 1,
                        "homepage": "https://nonebot.dev/",
                        "tags": [],
                        "type": "application",
                        "supported_adapters": None,
                        "metadata": {
                            "name": "TREEHELP",
                            "desc": "订阅牛客/CF/AT平台的比赛信息",
                            "homepage": "https://nonebot.dev/",
                            "type": "application",
                            "supported_adapters": None,
                        },
                    },
                    "errors": [
                        {
                            "type": "plugin.test",
                            "loc": ("load",),
                            "msg": "插件无法正常加载",
                            "input": False,
                            "ctx": {"output": None},
                        }
                    ],
                },
                "load": [
                    "创建测试目录 plugin_test",
                    "项目 nonebot-plugin_acm_reminder 创建成功。",
                    "    \x1b[39;1mVirtualenv\x1b[39;22m",
                    "    \x1b[34mPython\x1b[39m:         \x1b[32m3.11.10\x1b[39m",
                    "    \x1b[34mImplementation\x1b[39m: \x1b[32mCPython\x1b[39m",
                    "    \x1b[34mPath\x1b[39m:           \x1b[32mNA\x1b[39m",
                    "    \x1b[34mExecutable\x1b[39m:     \x1b[32mNA\x1b[39m",
                    "    ",
                    "    \x1b[39;1mBase\x1b[39;22m",
                    "    \x1b[34mPlatform\x1b[39m:   \x1b[32mlinux\x1b[39m",
                    "    \x1b[34mOS\x1b[39m:         \x1b[32mposix\x1b[39m",
                    "    \x1b[34mPython\x1b[39m:     \x1b[32m3.11.10\x1b[39m",
                    "    \x1b[34mPath\x1b[39m:       \x1b[32m/usr/local\x1b[39m",
                    "    \x1b[34mExecutable\x1b[39m: \x1b[32m/usr/local/bin/python3.11\x1b[39m",
                    "    Using version ^0.2.0 for nonebot-plugin-acm-reminder",
                    "    ",
                    "    Updating dependencies",
                    "    Resolving dependencies...",
                    "    ",
                    "    Package operations: 46 installs, 0 updates, 0 removals",
                    "    ",
                    "      - Installing typing-extensions (4.12.2)",
                    "      - Installing annotated-types (0.7.0)",
                    "      - Installing idna (3.10)",
                    "      - Installing multidict (6.1.0)",
                    "      - Installing propcache (0.2.0)",
                    "      - Installing pydantic-core (2.23.4)",
                    "      - Installing tarina (0.5.8)",
                    "      - Installing loguru (0.7.2)",
                    "      - Installing nepattern (0.7.6)",
                    "      - Installing pydantic (2.9.2)",
                    "      - Installing pygtrie (2.5.0)",
                    "      - Installing python-dotenv (1.0.1)",
                    "      - Installing yarl (1.14.0)",
                    "      - Installing arclet-alconna (1.8.30)",
                    "      - Installing certifi (2024.8.30)",
                    "      - Installing greenlet (3.0.3)",
                    "      - Installing h11 (0.14.0)",
                    "      - Installing markdown (3.7)",
                    "      - Installing markupsafe (3.0.1)",
                    "      - Installing nonebot2 (2.3.3)",
                    "      - Installing pyee (12.0.0)",
                    "      - Installing pytz (2024.2)",
                    "      - Installing pyyaml (6.0.2)",
                    "      - Installing six (1.16.0)",
                    "      - Installing sniffio (1.3.1)",
                    "      - Installing tzlocal (5.2)",
                    "      - Installing zipp (3.20.2)",
                    "      - Installing aiofiles (24.1.0)",
                    "      - Installing anyio (4.6.0)",
                    "      - Installing apscheduler (3.10.4)",
                    "      - Installing arclet-alconna-tools (0.7.9)",
                    "      - Installing httpcore (1.0.6)",
                    "      - Installing importlib-metadata (8.5.0)",
                    "      - Installing jinja2 (3.1.4)",
                    "      - Installing nonebot-plugin-waiter (0.8.0)",
                    "      - Installing playwright (1.47.0)",
                    "      - Installing pygments (2.18.0)",
                    "      - Installing pymdown-extensions (10.11.2)",
                    "      - Installing python-markdown-math (0.8)",
                    "      - Installing soupsieve (2.6)",
                    "      - Installing beautifulsoup4 (4.12.3)",
                    "      - Installing httpx (0.27.2)",
                    "      - Installing nonebot-plugin-alconna (0.53.0)",
                    "      - Installing nonebot-plugin-apscheduler (0.5.0)",
                    "      - Installing nonebot-plugin-htmlrender (0.3.5)",
                    "      - Installing nonebot-plugin-acm-reminder (0.2.0)",
                    "    ",
                    "    Writing lock file",
                    "插件 nonebot-plugin_acm_reminder 依赖的插件如下：",
                    "    nonebot_plugin_acm_reminder, nonebot_plugin_alconna, nonebot_plugin_apscheduler, nonebot_plugin_htmlrender, nonebot_plugin_waiter",
                    "插件 nonebot-plugin_acm_reminder 的信息如下：",
                    "    name         : nonebot-plugin-acm-reminder                                              ",
                    "     version      : 0.2.0                                                                    ",
                    "     description  : A subscribe CodeForces/NowCoder/Atcoder contest info plugin for nonebot2 ",
                    "    ",
                    "    dependencies",
                    "     - BeautifulSoup4 >=4.12.3",
                    "     - httpx >=0.23.3",
                    "     - nonebot-plugin-alconna >=0.42.0",
                    "     - nonebot-plugin-apscheduler >=0.2.0",
                    "     - nonebot-plugin-htmlrender >=0.2.0.3",
                    "     - nonebot2 >=2.2.1",
                    "     - pydantic >=2.6.4",
                    "插件 nonebot_plugin_acm_reminder 加载正常：",
                    "    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | NoneBot is initializing...",
                    "    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[1mINFO\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Current \x1b[33m\x1b[1mEnv: prod\x1b[0m\x1b[33m\x1b[0m",
                    '    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_apscheduler\x1b[0m"',
                    '    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_htmlrender\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_alconna:uniseg\x1b[0m" from "\x1b[35mnonebot_plugin_alconna.uniseg\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_alconna\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_acm_reminder\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_waiter\x1b[0m"',
                    "    /tmp/plugin_test/nonebot-plugin_acm_reminder-nonebot_plugin_acm_reminder/.venv/lib/python3.11/site-packages/nonebot_plugin_acm_reminder/__init__.py:13: RuntimeWarning: No adapters found, please make sure you have installed at least one adapter.",
                    '      require("nonebot_plugin_alconna")',
                ],
                "metadata": Metadata(
                    desc="订阅牛客/CF/AT平台的比赛信息",
                    homepage="https://nonebot.dev/",
                    name="TREEHELP",
                    supported_adapters=None,
                    type="application",
                ),
            },
            results={"validation": False, "load": False, "metadata": True},
            test_env={"unknown": True},
            version="0.2.0",
        )
    )

    assert new_plugin is None

    assert mocked_api["homepage"].called


async def test_validate_plugin_failed_with_previous(
    tmp_path: Path, mocked_api: MockRouter, mocker: MockerFixture
) -> None:
    """插件验证失败，但提供了之前插件信息的情况"""
    from src.providers.store_test.validation import StorePlugin, validate_plugin
    from src.providers.store_test.models import (
        TestResult,
        Metadata,
        Plugin,
    )

    mock_datetime = mocker.patch("src.providers.store_test.models.datetime")
    mock_datetime.now.return_value = datetime(
        2023, 8, 23, 9, 22, 14, 836035, tzinfo=ZoneInfo("Asia/Shanghai")
    )

    output_path = Path(__file__).parent / "output.json"
    mock_plugin_test = mock_docker_result(output_path, mocker)
    mock_plugin_test.run.return_value.load = False
    mocker.patch(
        "src.providers.store_test.validation.DockerPluginTest",
        return_value=mock_plugin_test,
    )

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
        False,
        previous_plugin=Plugin(
            module_name="module_name",
            project_link="project_link",
            name="name",
            author="author",
            author_id=1,
            desc="desc",
            homepage="homepage",
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
        TestResult(
            config="",
            outputs={
                "validation": {
                    "data": {
                        "module_name": "module_name",
                        "project_link": "project_link",
                        "name": "TREEHELP",
                        "desc": "订阅牛客/CF/AT平台的比赛信息",
                        "author": "he0119",
                        "author_id": 1,
                        "homepage": "https://nonebot.dev/",
                        "tags": [],
                        "type": "application",
                        "supported_adapters": None,
                        "metadata": {
                            "name": "TREEHELP",
                            "desc": "订阅牛客/CF/AT平台的比赛信息",
                            "homepage": "https://nonebot.dev/",
                            "type": "application",
                            "supported_adapters": None,
                        },
                    },
                    "errors": [
                        {
                            "type": "plugin.test",
                            "loc": ("load",),
                            "msg": "插件无法正常加载",
                            "input": False,
                            "ctx": {"output": None},
                        }
                    ],
                },
                "load": [
                    "创建测试目录 plugin_test",
                    "项目 nonebot-plugin_acm_reminder 创建成功。",
                    "    \x1b[39;1mVirtualenv\x1b[39;22m",
                    "    \x1b[34mPython\x1b[39m:         \x1b[32m3.11.10\x1b[39m",
                    "    \x1b[34mImplementation\x1b[39m: \x1b[32mCPython\x1b[39m",
                    "    \x1b[34mPath\x1b[39m:           \x1b[32mNA\x1b[39m",
                    "    \x1b[34mExecutable\x1b[39m:     \x1b[32mNA\x1b[39m",
                    "    ",
                    "    \x1b[39;1mBase\x1b[39;22m",
                    "    \x1b[34mPlatform\x1b[39m:   \x1b[32mlinux\x1b[39m",
                    "    \x1b[34mOS\x1b[39m:         \x1b[32mposix\x1b[39m",
                    "    \x1b[34mPython\x1b[39m:     \x1b[32m3.11.10\x1b[39m",
                    "    \x1b[34mPath\x1b[39m:       \x1b[32m/usr/local\x1b[39m",
                    "    \x1b[34mExecutable\x1b[39m: \x1b[32m/usr/local/bin/python3.11\x1b[39m",
                    "    Using version ^0.2.0 for nonebot-plugin-acm-reminder",
                    "    ",
                    "    Updating dependencies",
                    "    Resolving dependencies...",
                    "    ",
                    "    Package operations: 46 installs, 0 updates, 0 removals",
                    "    ",
                    "      - Installing typing-extensions (4.12.2)",
                    "      - Installing annotated-types (0.7.0)",
                    "      - Installing idna (3.10)",
                    "      - Installing multidict (6.1.0)",
                    "      - Installing propcache (0.2.0)",
                    "      - Installing pydantic-core (2.23.4)",
                    "      - Installing tarina (0.5.8)",
                    "      - Installing loguru (0.7.2)",
                    "      - Installing nepattern (0.7.6)",
                    "      - Installing pydantic (2.9.2)",
                    "      - Installing pygtrie (2.5.0)",
                    "      - Installing python-dotenv (1.0.1)",
                    "      - Installing yarl (1.14.0)",
                    "      - Installing arclet-alconna (1.8.30)",
                    "      - Installing certifi (2024.8.30)",
                    "      - Installing greenlet (3.0.3)",
                    "      - Installing h11 (0.14.0)",
                    "      - Installing markdown (3.7)",
                    "      - Installing markupsafe (3.0.1)",
                    "      - Installing nonebot2 (2.3.3)",
                    "      - Installing pyee (12.0.0)",
                    "      - Installing pytz (2024.2)",
                    "      - Installing pyyaml (6.0.2)",
                    "      - Installing six (1.16.0)",
                    "      - Installing sniffio (1.3.1)",
                    "      - Installing tzlocal (5.2)",
                    "      - Installing zipp (3.20.2)",
                    "      - Installing aiofiles (24.1.0)",
                    "      - Installing anyio (4.6.0)",
                    "      - Installing apscheduler (3.10.4)",
                    "      - Installing arclet-alconna-tools (0.7.9)",
                    "      - Installing httpcore (1.0.6)",
                    "      - Installing importlib-metadata (8.5.0)",
                    "      - Installing jinja2 (3.1.4)",
                    "      - Installing nonebot-plugin-waiter (0.8.0)",
                    "      - Installing playwright (1.47.0)",
                    "      - Installing pygments (2.18.0)",
                    "      - Installing pymdown-extensions (10.11.2)",
                    "      - Installing python-markdown-math (0.8)",
                    "      - Installing soupsieve (2.6)",
                    "      - Installing beautifulsoup4 (4.12.3)",
                    "      - Installing httpx (0.27.2)",
                    "      - Installing nonebot-plugin-alconna (0.53.0)",
                    "      - Installing nonebot-plugin-apscheduler (0.5.0)",
                    "      - Installing nonebot-plugin-htmlrender (0.3.5)",
                    "      - Installing nonebot-plugin-acm-reminder (0.2.0)",
                    "    ",
                    "    Writing lock file",
                    "插件 nonebot-plugin_acm_reminder 依赖的插件如下：",
                    "    nonebot_plugin_acm_reminder, nonebot_plugin_alconna, nonebot_plugin_apscheduler, nonebot_plugin_htmlrender, nonebot_plugin_waiter",
                    "插件 nonebot-plugin_acm_reminder 的信息如下：",
                    "    name         : nonebot-plugin-acm-reminder                                              ",
                    "     version      : 0.2.0                                                                    ",
                    "     description  : A subscribe CodeForces/NowCoder/Atcoder contest info plugin for nonebot2 ",
                    "    ",
                    "    dependencies",
                    "     - BeautifulSoup4 >=4.12.3",
                    "     - httpx >=0.23.3",
                    "     - nonebot-plugin-alconna >=0.42.0",
                    "     - nonebot-plugin-apscheduler >=0.2.0",
                    "     - nonebot-plugin-htmlrender >=0.2.0.3",
                    "     - nonebot2 >=2.2.1",
                    "     - pydantic >=2.6.4",
                    "插件 nonebot_plugin_acm_reminder 加载正常：",
                    "    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | NoneBot is initializing...",
                    "    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[1mINFO\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Current \x1b[33m\x1b[1mEnv: prod\x1b[0m\x1b[33m\x1b[0m",
                    '    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_apscheduler\x1b[0m"',
                    '    \x1b[32m10-10 14:21:07\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_htmlrender\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_alconna:uniseg\x1b[0m" from "\x1b[35mnonebot_plugin_alconna.uniseg\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_alconna\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_acm_reminder\x1b[0m"',
                    '    \x1b[32m10-10 14:21:08\x1b[0m [\x1b[32m\x1b[1mSUCCESS\x1b[0m] \x1b[36m\x1b[4mnonebot\x1b[0m\x1b[36m\x1b[0m | Succeeded to load plugin "\x1b[33mnonebot_plugin_waiter\x1b[0m"',
                    "    /tmp/plugin_test/nonebot-plugin_acm_reminder-nonebot_plugin_acm_reminder/.venv/lib/python3.11/site-packages/nonebot_plugin_acm_reminder/__init__.py:13: RuntimeWarning: No adapters found, please make sure you have installed at least one adapter.",
                    '      require("nonebot_plugin_alconna")',
                ],
                "metadata": Metadata(
                    desc="订阅牛客/CF/AT平台的比赛信息",
                    homepage="https://nonebot.dev/",
                    name="TREEHELP",
                    supported_adapters=None,
                    type="application",
                ),
            },
            results={"validation": False, "load": False, "metadata": True},
            test_env={"unknown": True},
            version="0.2.0",
        )
    )

    assert new_plugin == snapshot(
        Plugin(
            author="author",
            author_id=1,
            desc="desc",
            homepage="homepage",
            is_official=False,
            module_name="module_name",
            name="name",
            project_link="project_link",
            skip_test=False,
            supported_adapters=None,
            tags=[],
            time="2023-09-01T00:00:00+00:00Z",
            type="application",
            valid=False,
            version="0.2.0",
        )
    )

    assert mocked_api["homepage"].called
