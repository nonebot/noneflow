""" 验证数据是否符合规范 """

from typing import Any

from pydantic import validate_model

from .models import AdapterPublishInfo, BotPublishInfo, PluginPublishInfo, PublishType
from .results import ValidationResult

validation_model_map = {
    PublishType.BOT: BotPublishInfo,
    PublishType.ADAPTER: AdapterPublishInfo,
    PublishType.PLUGIN: PluginPublishInfo,
}


def validate_info(publish_type: PublishType, data: dict[str, Any]) -> ValidationResult:
    """验证信息是否符合规范"""
    if publish_type not in validation_model_map:
        raise ValueError("⚠️ 未知的发布类型。")

    data, fields_set, errors = validate_model(validation_model_map[publish_type], data)

    return ValidationResult(
        publish_type=publish_type, data=data, fields_set=fields_set, errors=errors
    )
