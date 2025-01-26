from datetime import datetime
from pathlib import Path

from inline_snapshot import snapshot
from pytest_mock import MockerFixture
from respx import MockRouter


async def test_step_summary(
    mocked_store_data: dict[str, Path],
    mocked_api: MockRouter,
    mocker: MockerFixture,
    mock_datetime,
) -> None:
    """验证插件信息"""
    from src.providers.models import StoreTestResult
    from src.providers.store_test.store import StoreTest

    store_test = {
        "NOT_AC": StoreTestResult(
            config="",
            outputs={
                "validation": None,
                "load": """\
创建测试目录 plugin_test
        For further information visit https://errors.pydantic.dev/2.9/v/model_type\x1b[0m\
""",
                "metadata": None,
            },
            results={"validation": True, "load": False, "metadata": False},
            test_env={"unknown": True},
            version="0.3.9",
        ),
        "TREEHELP": StoreTestResult(
            config="",
            outputs={
                "validation": None,
                "load": """\
创建测试目录 plugin_test
      require("nonebot_plugin_alconna")\
""",
                "metadata": {
                    "name": "TREEHELP",
                    "desc": "订阅牛客/CF/AT平台的比赛信息",
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
            test_env={"unknown": True},
            version="0.2.0",
        ),
    }

    store = StoreTest()
    assert snapshot(
        """\
# 📃 商店测试结果

> 📅 2023-08-23 09:22:14 CST
> ♻️ 共测试 2 个插件
> ✅ 更新成功：1 个
> ❌ 更新失败：1 个

## 通过测试插件列表

- TREEHELP

## 未通过测试插件列表

- NOT_AC
"""
    ) == store.generate_github_summary(results=store_test)
