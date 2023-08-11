from typing import TYPE_CHECKING, Any, Literal, TypedDict

from pydantic import ValidationError

from .models import PublishType

if TYPE_CHECKING:
    from pydantic.error_wrappers import ErrorDict


class ValidationDict(TypedDict):
    """验证结果字典"""

    type: Literal["pass", "fail"]
    name: str
    data: Any
    msg: str
    hint: str


class ValidationResult:
    """信息验证结果"""

    def __init__(
        self,
        publish_type: PublishType,
        data: dict[str, Any],
        fields_set: set,
        errors: ValidationError | None,
    ):
        self.type = publish_type
        self.data = data
        self.fields_set = fields_set
        self.error = errors

        self.results = self.parse_results()

    def parse_results(self) -> list[ValidationDict]:
        """解析验证结果"""
        if self.fields_set:
            return []

        if not self.error:
            return []

        results = []
        for error in self.error.errors():
            if "ctx" not in error:
                continue
            results.append(self.parse_error(error))
        return results

    def parse_error(self, error: "ErrorDict") -> ValidationDict:
        ...

    def render_issue_comment(self):
        ...

    def render_registry_message(self):
        ...
