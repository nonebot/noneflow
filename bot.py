from pathlib import Path
from typing import cast

import nonebot
from nonebot.adapters.github import Adapter as GITHUBAdapter
from nonebot.adapters.github import Event, events
from nonebot.adapters.github.bot import GitHubBot, OAuthBot
from nonebot.adapters.github.config import GitHubApp, OAuthApp
from nonebot.adapters.github.utils import log
from nonebot.drivers.none import Driver


class Adapter(GITHUBAdapter):
    def _setup(self):
        self.driver.on_startup(self._startup)

    async def _startup_app(self, app: GitHubApp | OAuthApp):
        if isinstance(app, GitHubApp):
            bot = GitHubBot(self, app)
            await bot._get_self_info()
        else:
            bot = OAuthBot(self, app)
        self.bot_connect(bot)

        # 从环境变量中获取事件信息
        event_id = self.config.github_run_id
        event_name = self.config.github_event_name
        github_event_path = Path(self.config.github_event_path)
        if event := self.payload_to_event(
            event_id, event_name, github_event_path.read_text(encoding="utf-8")
        ):
            # 处理一次之后就退出
            await bot.handle_event(event)
            driver = cast(Driver, self.driver)
            driver.should_exit.set()

    @classmethod
    def payload_to_event(
        cls, event_id: str, event_name: str, payload: str | bytes
    ) -> Event | None:
        # webhook 事件中没有 pull_request_target，但是 actions 里有
        # githubkit.exception.WebhookTypeNotFound: pull_request_target
        if event_name == "pull_request_target":
            event_name = "pull_request"

        return super().payload_to_event(event_id, event_name, payload)


nonebot.init(driver="~none")

driver = nonebot.get_driver()
driver.register_adapter(Adapter)


nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":
    nonebot.run()
