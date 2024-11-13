from pathlib import Path

from inline_snapshot import snapshot


async def test_json5_dump(tmp_path: Path) -> None:
    """输出 JSON5

    有尾随逗号
    """
    from src.providers.utils import dump_json5

    data = [
        {
            "name": "name",
            "desc": "desc",
            "author": "author",
            "homepage": "https://nonebot.dev",
            "tags": '[{"label": "test", "color": "#ffffff"}]',
            "author_id": 1,
        }
    ]

    test_file = tmp_path / "test.json5"
    dump_json5(test_file, data)

    assert test_file.read_text() == snapshot(
        """\
[
  {
    "name": "name",
    "desc": "desc",
    "author": "author",
    "homepage": "https://nonebot.dev",
    "tags": "[{\\"label\\": \\"test\\", \\"color\\": \\"#ffffff\\"}]",
    "author_id": 1
  },
]
"""
    )


async def test_json5_dump_empty_list(tmp_path: Path) -> None:
    """空列表

    末尾也应该有换行
    """
    from src.providers.utils import dump_json5

    data = []

    test_file = tmp_path / "test.json5"
    dump_json5(test_file, data)

    assert test_file.read_text() == snapshot("[]\n")
