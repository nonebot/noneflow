import asyncio
import os

import click

from src.providers.logger import logger
from src.providers.models import RegistryUpdatePayload

from .store import StoreTest


@click.group()
@click.option("--debug/--no-debug", default=False)
def cli(debug: bool):
    logger.setLevel("DEBUG" if debug else "INFO")


@cli.command()
def registry_update():
    """商店更新"""
    # 通过环境变量传递插件配置
    payload = os.environ.get("REGISTRY_UPDATE_PAYLOAD")
    if not payload:
        logger.warning("未传入更新数据")
        return

    payload = RegistryUpdatePayload.model_validate_json(payload)
    data = payload.get_artifact_data()

    test = StoreTest()
    asyncio.run(test.registry_update(data))


@cli.command()
@click.option("-l", "--limit", default=1, show_default=True, help="测试插件数量")
@click.option("-o", "--offset", default=0, show_default=True, help="测试插件偏移量")
@click.option("-f", "--force", default=False, is_flag=True, help="强制重新测试")
@click.option("-k", "--key", default=None, show_default=True, help="测试插件标识符")
@click.option(
    "-r",
    "--recent",
    default=False,
    is_flag=True,
    help="按测试时间倒序排列，优先测试最近测试的插件",
)
def plugin_test(limit: int, offset: int, force: bool, key: str | None, recent: bool):
    """插件测试"""
    from .store import StoreTest

    test = StoreTest()

    if key:
        # 指定了 key，直接测试该插件
        asyncio.run(test.run_single_plugin(key, force))
    else:
        # 没有指定 key，根据 recent 参数决定测试顺序
        asyncio.run(test.run(limit, offset, force, recent))


if __name__ == "__main__":
    cli()
