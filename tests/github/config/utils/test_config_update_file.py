import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from inline_snapshot import snapshot
from nonebug import App
from pytest_mock import MockerFixture

from tests.github.utils import check_json_data


async def test_update_file(
    app: App,
    mocker: MockerFixture,
    tmp_path: Path,
    mock_results: dict[str, Path],
) -> None:
    from src.plugins.github.plugins.config.utils import update_file
    from src.providers.validation.models import (
        PluginPublishInfo,
        PublishType,
        ValidationDict,
    )

    # 更改当前工作目录为临时目录
    os.chdir(tmp_path)

    mock_datetime = mocker.patch("src.providers.models.datetime")
    mock_datetime.now.return_value = datetime(
        2023, 8, 23, 9, 22, 14, 836035, tzinfo=ZoneInfo("Asia/Shanghai")
    )

    raw_data = {
        "module_name": "nonebot_plugin_treehelp",
        "project_link": "nonebot-plugin-treehelp",
        "name": "帮助",
        "desc": "获取插件帮助信息",
        "author": "he0119",
        "author_id": 1,
        "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
        "tags": [],
        "is_official": False,
        "type": "application",
        "supported_adapters": None,
        "load": True,
        "skip_test": False,
        "test_config": "log_level=DEBUG",
        "test_output": "test_output",
        "time": "2023-01-01T00:00:00Z",
        "version": "1.0.0",
    }
    result = ValidationDict(
        type=PublishType.PLUGIN,
        raw_data=raw_data,
        valid_data=raw_data,
        info=PluginPublishInfo.model_construct(**raw_data),
        errors=[],
    )
    update_file(result)

    check_json_data(
        mock_results["plugins"],
        snapshot(
            [
                {
                    "module_name": "nonebot_plugin_treehelp",
                    "project_link": "nonebot-plugin-treehelp",
                    "name": "帮助",
                    "desc": "获取插件帮助信息",
                    "author": "he0119",
                    "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
                    "tags": [],
                    "is_official": False,
                    "type": "application",
                    "supported_adapters": None,
                    "valid": True,
                    "time": "2023-01-01T00:00:00Z",
                    "version": "1.0.0",
                    "skip_test": False,
                }
            ]
        ),
    )
    check_json_data(
        mock_results["results"],
        snapshot(
            {
                "nonebot-plugin-treehelp:nonebot_plugin_treehelp": {
                    "time": "2023-08-23T09:22:14.836035+08:00",
                    "config": "log_level=DEBUG",
                    "version": "1.0.0",
                    "test_env": {"python==3.12": True},
                    "results": {"validation": True, "load": True, "metadata": True},
                    "outputs": {
                        "validation": None,
                        "load": "test_output",
                        "metadata": {
                            "name": "帮助",
                            "desc": "获取插件帮助信息",
                            "homepage": "https://github.com/he0119/nonebot-plugin-treehelp",
                            "type": "application",
                            "supported_adapters": None,
                        },
                    },
                }
            }
        ),
    )
    check_json_data(
        mock_results["plugin_configs"],
        snapshot(
            {"nonebot-plugin-treehelp:nonebot_plugin_treehelp": "log_level=DEBUG"}
        ),
    )
