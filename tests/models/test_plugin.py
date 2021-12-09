from collections import OrderedDict

from src.models import PluginPublishInfo


def test_plugin_info() -> None:
    info = PluginPublishInfo(
        module_name="module_name",
        project_link="project_link",
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
        module_name="module_name",
        project_link="project_link",
    )
