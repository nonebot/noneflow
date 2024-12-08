import asyncio
import os

from .plugin_test import PluginTest


def main():
    """根据传入的环境变量进行测试

    PYTHON_VERSION 为运行测试的 Python 版本
    PROJECT_LINK 为插件的项目名
    MODULE_NAME 为插件的模块名
    PLUGIN_CONFIG 为该插件的配置
    """
    python_version = os.environ.get("PYTHON_VERSION", "")

    project_link = os.environ.get("PROJECT_LINK", "")
    module_name = os.environ.get("MODULE_NAME", "")
    plugin_config = os.environ.get("PLUGIN_CONFIG", None)

    plugin = PluginTest(python_version, project_link, module_name, plugin_config)

    asyncio.run(plugin.run())


if __name__ == "__main__":
    main()
