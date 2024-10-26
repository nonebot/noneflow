"""验证数据是否符合规范"""

from typing import Any

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from .models import AdapterPublishInfo, BotPublishInfo, PluginPublishInfo, PublishInfo
from .models import Metadata as Metadata
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
    if context is None:
        context = {}
    # 用来存放验证通过的数据
    context["valid_data"] = {}

    info: PublishInfo | None = None
    errors: list[ErrorDetails] = []

    try:
        info = validation_model_map[publish_type].model_validate(
            raw_data, context=context
        )
    except ValidationError as exc:
        errors = exc.errors()

    # 翻译错误
    errors = translate_errors(errors)

    return ValidationDict(
        type=publish_type,
        raw_data=raw_data,
        context=context,
        info=info,
        errors=errors,
    )
