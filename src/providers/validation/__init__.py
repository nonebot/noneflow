"""验证数据是否符合规范"""

from typing import Any
from pydantic import ValidationError
from pydantic_core import ErrorDetails

from .models import (
    AdapterPublishInfo,
    BotPublishInfo,
    PluginPublishInfo,
    PublishInfo,
)
from .models import PublishType as PublishType
from .models import ValidationDict as ValidationDict
from .utils import translate_errors

validation_model_map: dict[PublishType, type[PublishInfo]] = {
    PublishType.BOT: BotPublishInfo,
    PublishType.ADAPTER: AdapterPublishInfo,
    PublishType.PLUGIN: PluginPublishInfo,
}


def validate_info(
    publish_type: PublishType,
    raw_data: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> ValidationDict:
    """根据发布类型验证数据是否符合规范

    Args:
        publish_type (PublishType): 发布类型
        raw_data (dict[str, Any]): 原始数据
        context (dict[str, Any] | None, optional): 验证上下文. 默认为拥有 `valid_data` 字段的字典
    """

    validation_context = {
        "valid_data": {},
    }
    if context:
        validation_context.update(context)

    errors: list[ErrorDetails] = []
    # 如果升级至 pydantic 2 后，可以使用 validation-context
    # https://docs.pydantic.dev/latest/usage/validators/#validation-context
    try:
        data = (
            validation_model_map[publish_type]
            .model_validate(raw_data, context=validation_context)
            .model_dump()
        )
    except ValidationError as exc:
        errors = exc.errors()
        data: dict[str, Any] = validation_context["valid_data"]
    # 翻译错误
    errors = translate_errors(errors)
    return ValidationDict(
        valid=not errors,
        data=data,
        errors=errors,  # 方便插件使用的数据
        type=publish_type,
        name=data.get("name") or raw_data.get("name") or "",
        author=data.get("author", ""),
    )
