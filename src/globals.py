from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Settings


settings: "Settings"
skip_plugin_test: bool = False
""" 是否跳过插件测试 """
