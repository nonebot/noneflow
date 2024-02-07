import asyncio
import os

import click


@click.command()
@click.option("-l", "--limit", default=1, show_default=True, help="测试插件数量")
@click.option("-o", "--offset", default=0, show_default=True, help="测试插件偏移量")
@click.option("-f", "--force", is_flag=True, help="强制重新测试")
@click.option("-k", "--key", default=None, show_default=True, help="测试插件标识符")
def main(limit: int, offset: int, force: bool, key: str | None):
    from .store import StoreTest

    test = StoreTest(offset, limit, force)

    # 通过环境变量传递插件配置
    config = os.environ.get("PLUGIN_CONFIG")
    data = os.environ.get("PLUGIN_DATA")

    asyncio.run(test.run(key, config, data))


if __name__ == "__main__":
    main()
