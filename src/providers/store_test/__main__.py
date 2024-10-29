import asyncio
import os

import click

from src.providers.models import RegistryUpdatePayload

from .store import StoreTest


@click.group()
@click.option("--debug/--no-debug", default=False)
def cli(debug: bool):
    click.echo(f"调试模式已{'开启' if debug else '关闭'}")


@cli.command()
def registry_update():
    """商店更新"""
    # 通过环境变量传递插件配置
    payload = os.environ.get("REGISTRY_UPDATE_PAYLOAD")
    if not payload:
        click.echo("未传入更新数据")
        return

    payload = RegistryUpdatePayload.model_validate_json(payload)

    test = StoreTest()
    asyncio.run(test.registry_update(payload))


@cli.command()
@click.option("-l", "--limit", default=1, show_default=True, help="测试插件数量")
@click.option("-o", "--offset", default=0, show_default=True, help="测试插件偏移量")
@click.option("-f", "--force", default=False, is_flag=True, help="强制重新测试")
@click.option("-k", "--key", default=None, show_default=True, help="测试插件标识符")
def plugin_test(limit: int, offset: int, force: bool, key: str | None):
    """插件测试"""
    from .store import StoreTest

    test = StoreTest()

    if key:
        asyncio.run(test.run_single_plugin(key, force))
    else:
        asyncio.run(test.run(limit, offset, force))


if __name__ == "__main__":
    cli()
