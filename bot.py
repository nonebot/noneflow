import asyncio
import os
from contextlib import contextmanager
from pathlib import Path
from typing import cast

import nonebot
from nonebot import logger
from nonebot.adapters.github import Adapter as GITHUBAdapter
from nonebot.adapters.github import Event
from nonebot.drivers.none import Driver
from nonebot.message import handle_event


@contextmanager
def ensure_cwd(cwd: Path):
    current_cwd = Path.cwd()
    try:
        os.chdir(cwd)
        yield
    finally:
        os.chdir(current_cwd)


async def handle_github_action_event():
    """处理 GitHub Action 事件"""
    driver = cast(Driver, nonebot.get_driver())
    try:
        config = driver.config
        # 从环境变量中获取事件信息
        # 读取到的 gitub_run_id 会因为 nonebot 配置加载机制转成 int，需要转回 str
        event_id = str(config.github_run_id)
        event_name = config.github_event_name
        github_event_path = Path(config.github_event_path)
        # 生成事件
        if event := Adapter.payload_to_event(
            event_id, event_name, github_event_path.read_text(encoding="utf-8")
        ):
            bot = nonebot.get_bot()
            await handle_event(bot, event)
    except Exception:
        logger.exception("处理 GitHub Action 事件时出现异常")


handle_event_task = None


class Adapter(GITHUBAdapter):
    def _setup(self):
        self.driver.on_startup(self._startup)

    async def _startup(self):
        driver = cast(Driver, self.driver)
        try:
            await super()._startup()
        except Exception:
            logger.exception("启动 GitHub 适配器时出现异常")
            driver.exit(True)
            return

        # 完成启动后创建任务处理 GitHub Action 事件
        handle_event_task = asyncio.create_task(handle_github_action_event())
        # 处理完成之后就退出
        handle_event_task.add_done_callback(lambda _: driver.exit(True))

    @classmethod
    def payload_to_event(
        cls, event_id: str, event_name: str, payload: str | bytes
    ) -> Event | None:
        # webhook 事件中没有 pull_request_target，但是 actions 里有
        # githubkit.exception.WebhookTypeNotFound: pull_request_target
        if event_name == "pull_request_target":
            event_name = "pull_request"

        return super().payload_to_event(event_id, event_name, payload)


with ensure_cwd(Path(__file__).parent):
    app_id = os.environ.get("APP_ID")
    private_key = os.environ.get("PRIVATE_KEY")
    # https://docs.github.com/en/actions/learn-github-actions/contexts#runner-context
    # 如果设置时，值总是为 "1"
    runner_debug = os.environ.get("RUNNER_DEBUG", "0")

    nonebot.init(
        driver="~none",
        github_apps=[{"app_id": app_id, "private_key": private_key}],
        log_level="DEBUG" if runner_debug == "1" else "INFO",
    )

    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)

    nonebot.load_plugins("src/plugins")


if __name__ == "__main__":
    nonebot.run()
