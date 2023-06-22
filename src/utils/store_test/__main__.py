import argparse
from asyncio import run

import nonebot

from .constants import TEST_DIR

if not TEST_DIR.exists():
    TEST_DIR.mkdir()

plugins_path = TEST_DIR / "plugins.json"
if not plugins_path.exists():
    with open(plugins_path, "w", encoding="utf8") as f:
        f.write("[]")

# 初始化 NoneBot，否则无法从插件中导入所需的模块
nonebot.init(
    driver="~none",
    input_config={
        "base": "",
        "plugin_path": str(plugins_path),
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
    parser.add_argument("-f", "--force", action="store_true", help="强制重新测试")
    args = parser.parse_args()
    from .store import StoreTest

    test = StoreTest(args.offset, args.limit, args.force)
    await test.run()


if __name__ == "__main__":
    run(main())
