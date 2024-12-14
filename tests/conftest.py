from pathlib import Path

import httpx
import nonebot
import pytest
from nonebot.adapters.github import Adapter
from nonebug import NONEBOT_INIT_KWARGS
from nonebug.app import App
from pytest_asyncio import is_async_test
from pytest_mock import MockerFixture
from respx import MockRouter

from src.providers.constants import STORE_ADAPTERS_URL, STORE_PLUGINS_URL


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {
        "driver": "~none",
        "input_config": {
            "base": "master",
            "adapter_path": "adapter_path",
            "bot_path": "bot_path",
            "plugin_path": "plugin_path",
            "registry_repository": "owner/registry",
            "store_repository": "owner/store",
        },
        "github_repository": "owner/repo",
        "github_run_id": "123456",
        "github_event_path": "event_path",
        "github_apps": [],
        "github_step_summary": "step_summary",
    }


def pytest_collection_modifyitems(items: list[pytest.Item]):
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture(scope="session", autouse=True)
async def _after_nonebot_init(after_nonebot_init: None):
    # 加载适配器
    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)

    # 加载插件
    nonebot.load_plugins(str(Path(__file__).parent.parent.parent / "src" / "plugins"))


@pytest.fixture
async def app(
    app: App, tmp_path: Path, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
):
    from src.plugins.github import plugin_config
    from src.providers.utils import dump_json5

    adapter_path = tmp_path / "adapters.json5"
    dump_json5(
        adapter_path,
        [
            {
                "module_name": "module_name1",
                "project_link": "project_link1",
                "name": "name",
                "desc": "desc",
                "author_id": 1,
                "homepage": "https://v2.nonebot.dev",
                "tags": [],
                "is_official": False,
            }
        ],
    )
    bot_path = tmp_path / "bots.json5"
    dump_json5(
        bot_path,
        [
            {
                "name": "name",
                "desc": "desc",
                "author_id": 1,
                "homepage": "https://v2.nonebot.dev",
                "tags": [],
                "is_official": False,
            }
        ],
    )
    plugin_path = tmp_path / "plugins.json5"
    dump_json5(
        plugin_path,
        [
            {
                "module_name": "module_name1",
                "project_link": "project_link1",
                "author_id": 1,
                "tags": [],
                "is_official": False,
            }
        ],
    )

    mocker.patch.object(plugin_config.input_config, "adapter_path", adapter_path)
    mocker.patch.object(plugin_config.input_config, "bot_path", bot_path)
    mocker.patch.object(plugin_config.input_config, "plugin_path", plugin_path)
    mocker.patch.object(
        plugin_config, "github_step_summary", tmp_path / "step_summary.txt"
    )
    # NOTE: 由于 providers 中没有初始化 nonebot，所以不能使用插件中的配置，只能直接使用环境变量。
    # 以后需要想想办法，如果能通过 nb-cli 启动就好了。
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "step_summary.md"))

    yield app

    from src.providers.utils import get_pypi_data

    get_pypi_data.cache_clear()


@pytest.fixture(autouse=True)
def _clear_cache(app: App):
    """每次运行前都清除 cache"""
    from src.providers.validation.utils import get_url

    get_url.cache_clear()


@pytest.fixture
def mocked_api(respx_mock: MockRouter):
    respx_mock.get("exception", name="exception").mock(side_effect=httpx.ConnectError)
    respx_mock.get(
        "https://pypi.org/pypi/project_link/json", name="project_link"
    ).respond(
        json={
            "info": {"name": "project_link", "version": "0.0.1"},
            "urls": [{"upload_time_iso_8601": "2023-09-01T00:00:00+00:00"}],
        }
    )
    respx_mock.get(
        "https://pypi.org/pypi/project_link//json", name="project_link/"
    ).respond(
        json={
            "info": {"name": "project_link/", "version": "0.0.1"},
            "urls": [{"upload_time_iso_8601": "2023-10-01T00:00:00+00:00"}],
        }
    )
    respx_mock.get(
        "https://pypi.org/pypi/nonebot-plugin-treehelp/json",
        name="project_link_treehelp",
    ).respond(
        json={
            "info": {"name": "nonebot-plugin-treehelp", "version": "0.3.1"},
            "urls": [{"upload_time_iso_8601": "2021-08-01T00:00:00+00:00"}],
        }
    )
    respx_mock.get(
        "https://pypi.org/pypi/nonebot-plugin-datastore/json",
        name="project_link_datastore",
    ).respond(
        json={
            "info": {"name": "nonebot-plugin-datastore", "version": "1.0.0"},
        }
    )
    respx_mock.get(
        "https://pypi.org/pypi/nonebot-plugin-wordcloud/json",
        name="project_link_wordcloud",
    ).respond(
        json={"info": {"name": "nonebot-plugin-wordcloud", "version": "0.5.0"}},
    )
    respx_mock.get(
        "https://pypi.org/pypi/project_link1/json", name="project_link1"
    ).respond(
        json={
            "info": {"name": "project_link1", "version": "0.5.0"},
            "urls": [{"upload_time_iso_8601": "2023-10-01T00:00:00+00:00"}],
        }
    )
    respx_mock.get(
        "https://pypi.org/pypi/project_link_failed/json", name="project_link_failed"
    ).respond(404)
    respx_mock.get(
        "https://pypi.org/pypi/project_link_normalization/json",
        name="project_link_normalization",
    ).respond(
        json={
            "info": {"name": "project-link-normalization", "version": "0.0.1"},
            "urls": [{"upload_time_iso_8601": "2023-10-01T00:00:00+00:00"}],
        }
    )
    respx_mock.get("https://www.baidu.com", name="homepage_failed").respond(404)
    respx_mock.get("https://nonebot.dev/", name="homepage").respond()
    respx_mock.get("https://v2.nonebot.dev", name="homepage_v2").respond()
    respx_mock.get(STORE_ADAPTERS_URL, name="store_adapters").respond(
        json=[
            {
                "module_name": "nonebot.adapters.onebot.v11",
                "project_link": "nonebot-adapter-onebot",
                "name": "OneBot V11",
                "desc": "OneBot V11 协议",
                "author_id": 2,
                "homepage": "https://onebot.adapters.nonebot.dev/",
                "tags": [],
                "is_official": True,
            },
            {
                "module_name": "nonebot.adapters.onebot.v12",
                "project_link": "nonebot-adapter-onebot",
                "name": "OneBot V12",
                "desc": "OneBot V12 协议",
                "author_id": 2,
                "homepage": "https://onebot.adapters.nonebot.dev/",
                "tags": [],
                "is_official": True,
            },
        ]
    )
    respx_mock.get(STORE_PLUGINS_URL, name="store_plugins").respond(
        json=[
            {
                "module_name": "nonebot-plugin-treehelp",
                "project_link": "nonebot-plugin-treehelp",
                "author_id": 1,
                "tags": [],
                "is_official": True,
            },
        ]
    )
    respx_mock.get("https://api.github.com/user/1", name="github_username_1").respond(
        json={"login": "he0119"}
    )
    respx_mock.get("https://api.github.com/user/2", name="github_username_2").respond(
        json={"login": "BigOrangeQWQ"}
    )
    return respx_mock
