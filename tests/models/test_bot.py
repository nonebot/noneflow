from collections import OrderedDict

from src.models import BotPublishInfo


def test_bot_info() -> None:
    info = BotPublishInfo(
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
    )

    assert OrderedDict(info.dict()) == OrderedDict(
        name="name",
        desc="desc",
        author="author",
        homepage="https://www.baidu.com",
        tags=["tag"],
        is_official=False,
    )
