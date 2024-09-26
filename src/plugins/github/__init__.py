from pathlib import Path

import nonebot

from .config import Config

plugin_config = nonebot.get_plugin_config(Config)

# 加载子插件
sub_plugins = nonebot.load_plugins(str((Path(__file__).parent / "plugins").resolve()))
