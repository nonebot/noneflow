from nonebug import App


async def test_missing_info():
    """测试缺失信息的情况

    https://github.com/nonebot/nonebot2/issues/900
    """
    from src.plugins.publish.constants import (  # GitHub 获取的是 body 为 \r\n
        PLUGIN_DESC_PATTERN,
        PLUGIN_HOMEPAGE_PATTERN,
        PLUGIN_MODULE_NAME_PATTERN,
        PLUGIN_NAME_PATTERN,
        PROJECT_LINK_PATTERN,
        TAGS_PATTERN,
    )

    body = """### 插件名称\r\n\r\n监测群事件\r\n\r\n### 插件描述\r\n\r\n监测群成员变动、文件上传、红包运气王、管理员变动等等...\r\n\r\n### PyPI 项目名\r\n\r\n\r\n\r\n### 插件 import 包名\r\n\r\n\r\n\r\n### 插件项目仓库/主页链接\r\n\r\nhttps://github.com/cjladmin/nonebot_plugin_monitor\r\n\r\n### 标签\r\n\r\n[]"""

    module_name = PLUGIN_MODULE_NAME_PATTERN.search(body)
    project_link = PROJECT_LINK_PATTERN.search(body)
    name = PLUGIN_NAME_PATTERN.search(body)
    desc = PLUGIN_DESC_PATTERN.search(body)
    homepage = PLUGIN_HOMEPAGE_PATTERN.search(body)
    tags = TAGS_PATTERN.search(body)

    assert module_name is None
    assert project_link is None

    assert name is not None
    assert name.group(1).strip() == "监测群事件"

    assert desc is not None
    assert desc.group(1).strip() == "监测群成员变动、文件上传、红包运气王、管理员变动等等..."

    assert homepage is not None
    assert (
        homepage.group(1).strip()
        == "https://github.com/cjladmin/nonebot_plugin_monitor"
    )

    assert tags is not None
    assert tags.group(1).strip() == "[]"
