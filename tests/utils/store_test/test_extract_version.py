from pathlib import Path


def test_extract_version(tmp_path: Path):
    """poetry show 的输出"""
    from src.utils.store_test.validation import extract_version

    with open(tmp_path / "output.txt", "w", encoding="utf8") as f:
        f.write(
            """
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
        )

    version = extract_version(tmp_path, "nonebot2")
    assert version == "2.0.1"


def test_extract_version_failed(tmp_path: Path):
    """版本解析失败的情况"""
    from src.utils.store_test.validation import extract_version

    with open(tmp_path / "output.txt", "w", encoding="utf8") as f:
        f.write(
            """
项目 nonebot-plugin-mockingbird 创建失败：
    Creating virtualenv nonebot-plugin-mockingbird-nonebot-plugin-mockingbird-test in /home/runner/work/registry/registry/plugin_test/nonebot-plugin-mockingbird-nonebot_plugin_mockingbird-test/.venv

    The current project's Python requirement (>=3.10,<3.11) is not compatible with some of the required packages Python requirement:
      - nonebot-plugin-mockingbird requires Python >=3.8,<3.10, so it will not be satisfied for Python >=3.10,<3.11

    Because no versions of nonebot-plugin-mockingbird match >0.2.1,<0.3.0
     and nonebot-plugin-mockingbird (0.2.1) requires Python >=3.8,<3.10, nonebot-plugin-mockingbird is forbidden.
    So, because nonebot-plugin-mockingbird-nonebot-plugin-mockingbird-test depends on nonebot-plugin-mockingbird (^0.2.1), version solving failed.

      • Check your dependencies Python requirement: The Python requirement can be specified via the `python` or `markers` properties

        For nonebot-plugin-mockingbird, a possible solution would be to set the `python` property to "<empty>"

        https://python-poetry.org/docs/dependency-specification/#python-restricted-dependencies,
        https://python-poetry.org/docs/dependency-specification/#using-environment-markers
"""
        )

    version = extract_version(tmp_path, "nonebot-plugin-mockingbird")

    assert version == "0.2.1"

    version = extract_version(tmp_path, "nonebot_plugin_mockingbird")

    assert version == "0.2.1"

    version = extract_version(tmp_path, "nonebot2")

    assert version is None
