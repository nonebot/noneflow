from inline_snapshot import snapshot


def test_extract_single_pattern_match():
    """测试单个正则表达式匹配"""
    from src.plugins.github.plugins.publish.constants import PLUGIN_NAME_PATTERN
    from src.plugins.github.utils import extract_issue_info_from_issue

    body = """### 插件名称

test-plugin

### 其他内容

其他信息"""

    result = extract_issue_info_from_issue(
        {
            "name": PLUGIN_NAME_PATTERN,
        },
        body,
    )
    assert result == {"name": "test-plugin"}


def test_extract_multiple_patterns_match():
    """测试多个正则表达式匹配"""
    from src.plugins.github.plugins.publish.constants import (
        PLUGIN_DESC_PATTERN,
        PLUGIN_HOMEPAGE_PATTERN,
        PLUGIN_NAME_PATTERN,
    )
    from src.plugins.github.utils import extract_issue_info_from_issue

    body = """### 插件名称

test-plugin

### 插件描述

这是一个测试插件

### 插件项目仓库/主页链接

https://github.com/test/test-plugin"""

    result = extract_issue_info_from_issue(
        {
            "name": PLUGIN_NAME_PATTERN,
            "desc": PLUGIN_DESC_PATTERN,
            "homepage": PLUGIN_HOMEPAGE_PATTERN,
        },
        body,
    )

    assert result == {
        "name": "test-plugin",
        "desc": "这是一个测试插件",
        "homepage": "https://github.com/test/test-plugin",
    }


def test_extract_pattern_list_first_match():
    """测试模式列表匹配第一个匹配项"""
    from src.plugins.github.plugins.publish.constants import (
        PLUGIN_MODULE_IMPORT_PATTERN,
        PLUGIN_MODULE_NAME_PATTERN,
    )
    from src.plugins.github.utils import extract_issue_info_from_issue

    body = """### 插件模块名

test_plugin

### 插件 import 包名

test_plugin_import"""

    result = extract_issue_info_from_issue(
        {
            "module_name": [PLUGIN_MODULE_NAME_PATTERN, PLUGIN_MODULE_IMPORT_PATTERN],
        },
        body,
    )

    # 应该匹配第一个找到的模式
    assert result == {"module_name": "test_plugin"}


def test_extract_pattern_list_second_match():
    """测试模式列表匹配第二个匹配项"""
    from src.plugins.github.plugins.publish.constants import (
        PLUGIN_MODULE_IMPORT_PATTERN,
        PLUGIN_MODULE_NAME_PATTERN,
    )
    from src.plugins.github.utils import extract_issue_info_from_issue

    body = """### 插件 import 包名

test_plugin_import

### 其他信息

其他内容"""

    result = extract_issue_info_from_issue(
        {
            "module_name": [PLUGIN_MODULE_NAME_PATTERN, PLUGIN_MODULE_IMPORT_PATTERN],
        },
        body,
    )

    # 应该匹配第二个模式
    assert result == {"module_name": "test_plugin_import"}


def test_extract_no_match():
    """测试没有匹配项的情况"""
    from src.plugins.github.plugins.publish.constants import (
        PLUGIN_DESC_PATTERN,
        PLUGIN_NAME_PATTERN,
    )
    from src.plugins.github.utils import extract_issue_info_from_issue

    body = """### 其他标题

其他内容

### 另一个标题

另一个内容"""

    result = extract_issue_info_from_issue(
        {
            "name": PLUGIN_NAME_PATTERN,
            "desc": PLUGIN_DESC_PATTERN,
        },
        body,
    )

    # 没有匹配项，应该返回空字典
    assert result == {}


def test_extract_partial_match():
    """测试部分匹配的情况"""
    from src.plugins.github.plugins.publish.constants import (
        PLUGIN_DESC_PATTERN,
        PLUGIN_HOMEPAGE_PATTERN,
        PLUGIN_NAME_PATTERN,
    )
    from src.plugins.github.utils import extract_issue_info_from_issue

    body = """### 插件名称

test-plugin

### 插件描述

这是一个测试插件"""

    result = extract_issue_info_from_issue(
        {
            "name": PLUGIN_NAME_PATTERN,
            "desc": PLUGIN_DESC_PATTERN,
            "homepage": PLUGIN_HOMEPAGE_PATTERN,
        },
        body,
    )

    # 只有匹配的字段会被包含在结果中
    assert result == {
        "name": "test-plugin",
        "desc": "这是一个测试插件",
    }


def test_extract_with_whitespace_strip():
    """测试匹配结果会去除首尾空格"""
    from src.plugins.github.plugins.publish.constants import PLUGIN_NAME_PATTERN
    from src.plugins.github.utils import extract_issue_info_from_issue

    body = """### 插件名称

   test-plugin

### 其他内容

其他信息"""

    result = extract_issue_info_from_issue(
        {
            "name": PLUGIN_NAME_PATTERN,
        },
        body,
    )

    # 结果应该去除首尾空格
    assert result == {"name": "test-plugin"}


def test_extract_multiline_content():
    """测试多行内容的匹配"""
    from src.plugins.github.plugins.publish.constants import PLUGIN_CONFIG_PATTERN
    from src.plugins.github.utils import extract_issue_info_from_issue

    body = """### 插件配置项

```dotenv
LOG_LEVEL=DEBUG
API_KEY=test_key
TIMEOUT=30
```

### 其他内容

其他信息"""

    result = extract_issue_info_from_issue(
        {
            "config": PLUGIN_CONFIG_PATTERN,
        },
        body,
    )

    assert result == {"config": "LOG_LEVEL=DEBUG\nAPI_KEY=test_key\nTIMEOUT=30"}


def test_extract_empty_body():
    """测试空内容的情况"""
    from src.plugins.github.plugins.publish.constants import PLUGIN_NAME_PATTERN
    from src.plugins.github.utils import extract_issue_info_from_issue

    result = extract_issue_info_from_issue(
        {
            "name": PLUGIN_NAME_PATTERN,
        },
        "",
    )
    assert result == {}


def test_extract_real_world_plugin_example():
    """测试真实世界的插件示例"""
    from src.plugins.github.plugins.publish.constants import (
        PLUGIN_CONFIG_PATTERN,
        PLUGIN_MODULE_IMPORT_PATTERN,
        PLUGIN_MODULE_NAME_PATTERN,
        PROJECT_LINK_PATTERN,
        TAGS_PATTERN,
    )
    from src.plugins.github.utils import extract_issue_info_from_issue

    body = """### PyPI 项目名

nonebot-plugin-test

### 插件模块名

nonebot_plugin_test

### 标签

[{"label": "test", "color": "#ffffff"}]

### 插件配置项

```dotenv
LOG_LEVEL=DEBUG
TEST_MODE=true
```"""

    result = extract_issue_info_from_issue(
        {
            "module_name": [PLUGIN_MODULE_NAME_PATTERN, PLUGIN_MODULE_IMPORT_PATTERN],
            "project_link": PROJECT_LINK_PATTERN,
            "test_config": PLUGIN_CONFIG_PATTERN,
            "tags": TAGS_PATTERN,
        },
        body,
    )

    assert result == {
        "module_name": "nonebot_plugin_test",
        "project_link": "nonebot-plugin-test",
        "test_config": "LOG_LEVEL=DEBUG\nTEST_MODE=true",
        "tags": '[{"label": "test", "color": "#ffffff"}]',
    }


def test_extract_real_world_adapter_example():
    """测试真实世界的适配器示例"""
    from src.plugins.github.plugins.publish.constants import (
        ADAPTER_DESC_PATTERN,
        ADAPTER_HOMEPAGE_PATTERN,
        ADAPTER_MODULE_NAME_PATTERN,
        ADAPTER_NAME_PATTERN,
        PROJECT_LINK_PATTERN,
        TAGS_PATTERN,
    )
    from src.plugins.github.utils import extract_issue_info_from_issue

    body = """### 适配器名称

Test Adapter

### 适配器描述

一个用于测试的适配器

### PyPI 项目名

nonebot-adapter-test

### 适配器 import 包名

nonebot.adapters.test

### 适配器项目仓库/主页链接

https://github.com/nonebot/adapter-test

### 标签

[{"label": "adapter", "color": "#00ff00"}]"""

    result = extract_issue_info_from_issue(
        {
            "name": ADAPTER_NAME_PATTERN,
            "desc": ADAPTER_DESC_PATTERN,
            "module_name": ADAPTER_MODULE_NAME_PATTERN,
            "project_link": PROJECT_LINK_PATTERN,
            "homepage": ADAPTER_HOMEPAGE_PATTERN,
            "tags": TAGS_PATTERN,
        },
        body,
    )

    assert result == {
        "name": "Test Adapter",
        "desc": "一个用于测试的适配器",
        "module_name": "nonebot.adapters.test",
        "project_link": "nonebot-adapter-test",
        "homepage": "https://github.com/nonebot/adapter-test",
        "tags": '[{"label": "adapter", "color": "#00ff00"}]',
    }


def test_extract_real_world_bot_example():
    """测试真实世界的机器人示例"""
    from src.plugins.github.plugins.publish.constants import (
        BOT_DESC_PATTERN,
        BOT_HOMEPAGE_PATTERN,
        BOT_NAME_PATTERN,
        TAGS_PATTERN,
    )
    from src.plugins.github.utils import extract_issue_info_from_issue

    body = """### 机器人名称

测试机器人

### 机器人描述

这是一个用于测试的机器人

### 机器人项目仓库/主页链接

https://github.com/test/test-bot

### 标签

[{"label": "bot", "color": "#ff0000"}]"""

    result = extract_issue_info_from_issue(
        {
            "name": BOT_NAME_PATTERN,
            "desc": BOT_DESC_PATTERN,
            "homepage": BOT_HOMEPAGE_PATTERN,
            "tags": TAGS_PATTERN,
        },
        body,
    )

    assert result == {
        "name": "测试机器人",
        "desc": "这是一个用于测试的机器人",
        "homepage": "https://github.com/test/test-bot",
        "tags": '[{"label": "bot", "color": "#ff0000"}]',
    }


def test_extract_missing_info():
    """测试缺失信息的情况

    https://github.com/nonebot/nonebot2/issues/900
    """
    from src.plugins.github.plugins.publish.constants import (
        PLUGIN_DESC_PATTERN,
        PLUGIN_HOMEPAGE_PATTERN,
        PLUGIN_MODULE_NAME_PATTERN,
        PLUGIN_NAME_PATTERN,
        PROJECT_LINK_PATTERN,
        TAGS_PATTERN,
    )
    from src.plugins.github.utils import extract_issue_info_from_issue

    # GitHub 获取的是 body 为 \r\n
    body = """### 插件名称\r\n\r\n监测群事件\r\n\r\n### 插件描述\r\n\r\n监测群成员变动、文件上传、红包运气王、管理员变动等等...\r\n\r\n### PyPI 项目名\r\n\r\n\r\n\r\n### 插件模块名\r\n\r\n\r\n\r\n### 插件项目仓库/主页链接\r\n\r\nhttps://github.com/cjladmin/nonebot_plugin_monitor\r\n\r\n### 标签\r\n\r\n[]"""

    result = extract_issue_info_from_issue(
        {
            "module_name": PLUGIN_MODULE_NAME_PATTERN,
            "project_link": PROJECT_LINK_PATTERN,
            "name": PLUGIN_NAME_PATTERN,
            "desc": PLUGIN_DESC_PATTERN,
            "homepage": PLUGIN_HOMEPAGE_PATTERN,
            "tags": TAGS_PATTERN,
        },
        body,
    )

    assert result == snapshot(
        {
            "name": "监测群事件",
            "desc": "监测群成员变动、文件上传、红包运气王、管理员变动等等...",
            "homepage": "https://github.com/cjladmin/nonebot_plugin_monitor",
            "tags": "[]",
        }
    )
