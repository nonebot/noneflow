from pydantic import PydanticValueError


class CustomError(PydanticValueError):
    code = "custom"
    msg_template = "⚠️ {msg}<dt>{hint}</dt>"


class NameError(CustomError):
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
