from asyncio import run

import click
import nonebot

from .constants import MOCK_PLUGINS_PATH

# 初始化 NoneBot，否则无法从插件中导入所需的模块
nonebot.init(
    driver="~none",
    input_config={
        "base": "",
        "plugin_path": str(MOCK_PLUGINS_PATH),
        "bot_path": "plugin_test/temp/bots.json",
        "adapter_path": "plugin_test/temp/adapters.json",
        "registry_repository": "nonebot/plugin-test",
    },
    github_repository="nonebot/plugin-test",
    github_run_id=0,
    plugin_test_result="",
    plugin_test_output="",
)


@click.command()
@click.option("-l", "--limit", default=1, show_default=True, help="测试插件数量")
@click.option("-o", "--offset", default=0, show_default=True, help="测试插件偏移量")
@click.option("-f", "--force", is_flag=True, help="强制重新测试")
@click.option("-k", "--key", default=None, show_default=True, help="测试插件标识符")
def main(limit: int, offset: int, force: bool, key: str | None):
    from .store import StoreTest

    test = StoreTest(offset, limit, force)
    run(test.run(key))


if __name__ == "__main__":
    main()
