from inline_snapshot import snapshot
from nonebug import App


async def test_render_runner(app: App):
    """测试生成 runner.py 文件内容"""
    from src.providers.docker_test.render import render_runner

    comment = await render_runner("nonebot_plugin_treehelp", ["nonebot_plugin_alconna"])
    assert comment == snapshot(
        """\
import json

from nonebot import init, load_plugin, logger, require
from pydantic import BaseModel


class SetEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, set):
            return list(o)
        return json.JSONEncoder.default(self, o)


init()
plugin = load_plugin("nonebot_plugin_treehelp")

if not plugin:
    exit(1)
else:
    if plugin.metadata:
        metadata = {
            "name": plugin.metadata.name,
            "desc": plugin.metadata.description,
            "usage": plugin.metadata.usage,
            "type": plugin.metadata.type,
            "homepage": plugin.metadata.homepage,
            "supported_adapters": plugin.metadata.supported_adapters,
        }
        with open("metadata.json", "w", encoding="utf-8") as f:
            try:
                f.write(f"{json.dumps(metadata, cls=SetEncoder)}")
            except Exception:
                f.write("{}")

        if plugin.metadata.config and not issubclass(plugin.metadata.config, BaseModel):
            logger.error("插件配置项不是 Pydantic BaseModel 的子类")
            exit(1)

require("nonebot_plugin_alconna")
"""
    )


async def test_render_fake(app: App):
    """测试生成 fake.py 文件内容"""
    from src.providers.docker_test.render import render_fake

    comment = await render_fake()
    assert comment == snapshot(
        """\
from typing import Optional, Union
from collections.abc import AsyncGenerator
from nonebot import logger
from nonebot.drivers import (
    ASGIMixin,
    HTTPClientMixin,
    HTTPClientSession,
    HTTPVersion,
    Request,
    Response,
    WebSocketClientMixin,
)
from nonebot.drivers import Driver as BaseDriver
from nonebot.internal.driver.model import (
    CookieTypes,
    HeaderTypes,
    QueryTypes,
)
from typing_extensions import override


class Driver(BaseDriver, ASGIMixin, HTTPClientMixin, WebSocketClientMixin):
    @property
    @override
    def type(self) -> str:
        return "fake"

    @property
    @override
    def logger(self):
        return logger

    @override
    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)

    @property
    @override
    def server_app(self):
        return None

    @property
    @override
    def asgi(self):
        raise NotImplementedError

    @override
    def setup_http_server(self, setup):
        raise NotImplementedError

    @override
    def setup_websocket_server(self, setup):
        raise NotImplementedError

    @override
    async def request(self, setup: Request) -> Response:
        raise NotImplementedError

    @override
    async def websocket(self, setup: Request) -> Response:
        raise NotImplementedError

    @override
    async def stream_request(
        self,
        setup: Request,
        *,
        chunk_size: int = 1024,
    ) -> AsyncGenerator[Response, None]:
        raise NotImplementedError

    @override
    def get_session(
        self,
        params: QueryTypes = None,
        headers: HeaderTypes = None,
        cookies: CookieTypes = None,
        version: Union[str, HTTPVersion] = HTTPVersion.H11,
        timeout: Optional[float] = None,
        proxy: Optional[str] = None,
    ) -> HTTPClientSession:
        raise NotImplementedError
"""
    )
