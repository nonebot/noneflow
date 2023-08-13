from pydantic import PydanticValueError


class CustomError(PydanticValueError):
    code = "custom"

    def __str__(self) -> str:
        msg = self.__dict__.get("msg", "")
        hint = self.__dict__.get("hint", "")
        return f"{self.code}: {msg}{hint}"


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
