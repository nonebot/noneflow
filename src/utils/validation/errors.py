from pydantic import PydanticValueError

from .constants import MAX_NAME_LENGTH


class PublishNameError(PydanticValueError):
    code = "name"


class PublishNameTooLongError(PublishNameError):
    code = "name.too_long"
    msg_template = f"名称不能超过 {MAX_NAME_LENGTH} 个字符。"


class HomepageError(PydanticValueError):
    code = "homepage"


class HomepageUnreachableError(HomepageError):
    code = "homepage.unreachable"
    msg_template = "项目主页不可访问。"


class TagsError(PydanticValueError):
    code = "tags"


class TagsListError(TagsError):
    code = "tags.not_list"
    msg_template = "标签不是列表。"


class TagsDictError(TagsError):
    code = "tags.not_dict"
    msg_template = "标签列表内不全为字典。"


class TagsTooManyError(TagsError):
    code = "tags.too_many"
    msg_template = "标签数量超过 3 个。"


class TagError(PydanticValueError):
    code = "tag"


class TagLabelError(TagError):
    code = "tag.label"
    msg_template = "标签名称超过 10 个字符。"


class TagColorError(TagError):
    code = "tag.color"
    msg_template = "标签颜色不符合十六进制颜色码规则。"


class ModuleNameError(PydanticValueError):
    code = "module_name"
    msg_template = "包名不符合规范。"


class ProjectLinkError(PydanticValueError):
    code = "project_link"


class ProjectLinkNameError(ProjectLinkError):
    code = "project_link.name"
    msg_template = "PyPI 项目名不符合规范。"


class ProjectLinkNotFoundError(ProjectLinkError):
    code = "project_link.not_found"
    msg_template = "PyPI 项目名不存在。"


class DuplicationError(PydanticValueError):
    code = "duplication"
    msg_template = "PyPI 项目名 {project_link} 加包名 {module_name} 的值与商店重复。"

    def __init__(self, *, project_link: str, module_name: str) -> None:
        super().__init__(project_link=project_link, module_name=module_name)


class PluginTestError(PydanticValueError):
    code = "plugin.test"
    msg_template = "插件加载测试未通过。"


class PluginTypeError(PydanticValueError):
    code = "plugin.type"
    msg_template = "插件类型不符合规范。"


class PluginSupportedAdaptersError(PydanticValueError):
    code = "plugin.supported_adapters"


class PluginSupportedAdaptersMissingError(PydanticValueError):
    code = "plugin.supported_adapters.missing"
    msg_template = "适配器 {', '.join(missing_adapters)} 不存在。"

    def __init__(self, *, missing_adapters: set[str]) -> None:
        super().__init__(missing_adapters=missing_adapters)
