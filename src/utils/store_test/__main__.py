import argparse
from asyncio import run

import nonebot

# 初始化 NoneBot，否则无法从插件中导入所需的模块
nonebot.init(
    driver="~none",
    input_config={
        "base": "",
        "plugin_path": "plugin_test/plugins.json",
        "bot_path": "plugin_test/bots.json",
        "adapter_path": "plugin_test/adapters.json",
    },
    github_repository="nonebot/plugin-test",
    github_run_id=0,
    plugin_test_result="",
    plugin_test_output="",
)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--limit", type=int, default=1, help="测试插件数量")
    parser.add_argument("-o", "--offset", type=int, default=0, help="测试插件偏移量")
    args = parser.parse_args()
    from .store import StoreTest

    test = StoreTest(args.offset, args.limit)
    await test.run()


if __name__ == "__main__":
    run(main())
