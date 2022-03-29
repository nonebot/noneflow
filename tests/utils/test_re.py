from src.constants import (
    PLUGIN_DESC_PATTERN,
    PLUGIN_HOMEPAGE_PATTERN,
    PLUGIN_MODULE_NAME_PATTERN,
    PLUGIN_NAME_PATTERN,
    PROJECT_LINK_PATTERN,
    TAGS_PATTERN,
)


def test_missing_info():
    """测试缺失信息的情况

    https://github.com/nonebot/nonebot2/issues/900
    """
    body = """**插件名称：**\n\n监测群事件\n\n**插件功能：**\n\n监测群成员变动、文件上传、红包运气王、管理员变动等等...\n\n**PyPI 项目名：**\n\nnonebot_plugin_monitor\n\n**插件 import 包名：**\n\n\n\n**插件项目仓库/主页链接：**\n\nhttps://github.com/cjladmin/nonebot_plugin_monitor\n\n**标签：**\n\n[]\n"""

    module_name = PLUGIN_MODULE_NAME_PATTERN.search(body)
    project_link = PROJECT_LINK_PATTERN.search(body)
    name = PLUGIN_NAME_PATTERN.search(body)
    desc = PLUGIN_DESC_PATTERN.search(body)
    homepage = PLUGIN_HOMEPAGE_PATTERN.search(body)
    tags = TAGS_PATTERN.search(body)

    assert module_name is None

    assert project_link is not None
    assert project_link.group(1).strip() == "nonebot_plugin_monitor"

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
