from pydantic import PydanticValueError


class HomepageError(PydanticValueError):
    code = "homepage"
    msg_template = "项目主页无法访问"

    def __init__(self, status_code: int, msg: str) -> None:
        super().__init__(status_code=status_code, msg=msg)


class ModuleNameError(PydanticValueError):
    code = "module_name"
    msg_template = "包名不符合规范"


class ProjectLinkError(PydanticValueError):
    code = "project_link"


class ProjectLinkNameError(ProjectLinkError):
    code = "project_link.name"
    msg_template = "PyPI 项目名不符合规范"


class ProjectLinkNotFoundError(ProjectLinkError):
    code = "project_link.not_found"
    msg_template = "PyPI 项目名不存在"


class DuplicationError(PydanticValueError):
    code = "duplication"
    msg_template = "PyPI 项目名 {project_link} 加包名 {module_name} 的值与商店重复"

    def __init__(self, *, project_link: str, module_name: str) -> None:
        super().__init__(project_link=project_link, module_name=module_name)


class PluginTestError(PydanticValueError):
    code = "plugin.test"
    msg_template = "插件加载测试未通过"


class PluginTypeError(PydanticValueError):
    code = "plugin.type"
    msg_template = "插件类型不符合规范"


class PluginSupportedAdaptersMissingError(PydanticValueError):
    code = "plugin.supported_adapters.missing"

    def __init__(self, *, missing_adapters: set[str]) -> None:
        super().__init__(missing_adapters=missing_adapters)

    def __str__(self) -> str:
        return f"适配器 {', '.join(self.missing_adapters)} 不存在"  # type: ignore
