from pathlib import Path


def test_extract_version(tmp_path: Path):
    """poetry show 的输出"""
    from src.providers.docker_test.plugin_test import extract_version

    output = """
 name         : nonebot2
 version      : 2.0.1
 description  : An asynchronous python bot framework.

dependencies
 - httpx >=0.20.0,<1.0.0
 - loguru >=0.6.0,<1.0.0
 - pydantic >=1.10.0,<2.0.0
 - pygtrie >=2.4.1,<3.0.0
 - tomli >=2.0.1,<3.0.0
 - typing-extensions >=4.0.0,<5.0.0
 - yarl >=1.7.2,<2.0.0

required by
 - nonebot-adapter-github >=2.0.0-beta.5,<3.0.0
 - nonebug >=2.0.0-rc.2,<3.0.0
"""

    version = extract_version(output, "nonebot2")
    assert version == "2.0.1"


def test_extract_version_resolve_failed(tmp_path: Path):
    """版本解析失败的情况"""
    from src.providers.docker_test.plugin_test import extract_version

    output = """
项目 ELF-RSS 创建失败：
    Virtualenv
    Python:         3.12.7
    Implementation: CPython
    Path:           NA
    Executable:     NA

    Base
    Platform:   linux
    OS:         posix
    Python:     3.12.7
    Path:       /usr/local
    Executable: /usr/local/bin/python3.12
    Using version ^2.6.25 for elf-rss

    Updating dependencies
    Resolving dependencies...
    Creating virtualenv elf-rss-elf-rss2 in /tmp/plugin_test/ELF-RSS-ELF_RSS2/.venv

    The current project's supported Python range (>=3.12,<3.13) is not compatible with some of the required packages Python requirement:
      - elf-rss requires Python <4.0.0,>=3.12.6, so it will not be satisfied for Python >=3.12,<3.12.6

    Because no versions of elf-rss match >2.6.25,<3.0.0
     and elf-rss (2.6.25) requires Python <4.0.0,>=3.12.6, elf-rss is forbidden.
    So, because elf-rss-elf-rss2 depends on elf-rss (^2.6.25), version solving failed.

      • Check your dependencies Python requirement: The Python requirement can be specified via the `python` or `markers` properties

        For elf-rss, a possible solution would be to set the `python` property to ">=3.12.6,<3.13"

        https://python-poetry.org/docs/dependency-specification/#python-restricted-dependencies,
        https://python-poetry.org/docs/dependency-specification/#using-environment-markers
"""

    version = extract_version(output, "ELF-RSS")

    assert version == "2.6.25"

    version = extract_version(output, "nonebot2")

    assert version is None


def test_extract_version_install_failed(tmp_path: Path):
    """安装插件失败的情况"""
    from src.providers.docker_test.plugin_test import extract_version

    output = """
项目 nonebot-plugin-ncm 创建失败：
    Virtualenv
    Python:         3.12.7
    Implementation: CPython
    Path:           NA
    Executable:     NA

    Base
    Platform:   linux
    OS:         posix
    Python:     3.12.7
    Path:       /usr/local
    Executable: /usr/local/bin/python3.12
    Using version ^1.6.16 for nonebot-plugin-ncm

    Updating dependencies
    Resolving dependencies...

    Package operations: 32 installs, 0 updates, 0 removals
"""

    version = extract_version(output, "nonebot-plugin-ncm")

    assert version == "1.6.16"

    version = extract_version(output, "nonebot2")

    assert version is None
