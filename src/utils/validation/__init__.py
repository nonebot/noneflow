""" 验证数据是否符合规范 """

from typing import Any

from pydantic import ValidationError

from .models import (
    AdapterPublishInfo,
    BotPublishInfo,
    PluginPublishInfo,
    PublishInfo,
    PublishType,
)
from .results import ValidationResult


def validate_info(publish_type: PublishType, data: dict[str, Any]) -> ValidationResult:
    """验证信息是否符合规范"""
    info = None
    errors = None

    try:
        match publish_type:
            case PublishType.BOT:
                info = BotPublishInfo.parse_obj(data)
            case PublishType.ADAPTER:
                info = AdapterPublishInfo.parse_obj(data)
            case PublishType.PLUGIN:
                info = PluginPublishInfo.parse_obj(data)
            case _:
                raise ValueError("⚠️ 未知的发布类型。")
    except ValidationError as e:
        errors = e

    return ValidationResult(
        publish_type=publish_type, data=data, info=info, error=errors
    )
