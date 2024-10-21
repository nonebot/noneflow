import asyncio
import os

import click


@click.command()
@click.option("-l", "--limit", default=1, show_default=True, help="测试插件数量")
@click.option("-o", "--offset", default=0, show_default=True, help="测试插件偏移量")
@click.option("-f", "--force", default=False, is_flag=True, help="强制重新测试")
@click.option("-k", "--key", default=None, show_default=True, help="测试插件标识符")
def main(limit: int, offset: int, force: bool, key: str | None):
    from .store import StoreTest

    test = StoreTest()

    # 通过环境变量传递插件配置
    config = os.environ.get("PLUGIN_CONFIG")
    data = os.environ.get("PLUGIN_DATA")

    if key and (config or data):
        asyncio.run(test.run_single_plugin(key, force, data, config))
    else:
        asyncio.run(test.run(limit, force))


if __name__ == "__main__":
    main()
