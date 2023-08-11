from pydantic import PydanticValueError


class CustomError(PydanticValueError):
    code = "custom"
    msg_template = "⚠️ {msg}<dt>{hint}</dt>"


class PublishNameError(CustomError):
    code = "name"


class HomepageError(CustomError):
    code = "homepage"


class TagsError(CustomError):
    code = "tags"


class TagError(CustomError):
    code = "tag"


class ModuleNameError(CustomError):
    code = "module_name"


class ProjectLinkError(CustomError):
    code = "project_link"


class DuplicationError(CustomError):
    code = "duplication"


class PluginTestError(CustomError):
    code = "plugin_test"


class PluginTypeError(CustomError):
    code = "plugin_type"


class PluginSupportedAdaptersError(CustomError):
    code = "plugin_supported_adapters"
