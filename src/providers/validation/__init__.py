"""验证数据是否符合规范"""

from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from .models import (
    AdapterPublishInfo,
    BotPublishInfo,
    DriverPublishInfo,
    PluginPublishInfo,
)
from .models import PublishInfoModels as PublishInfoModels
from .models import PublishType as PublishType
from .models import ValidationDict as ValidationDict
from .utils import translate_errors

if TYPE_CHECKING:
    from pydantic_core import ErrorDetails

validation_model_map: dict[PublishType, type[PublishInfoModels]] = {
    PublishType.BOT: BotPublishInfo,
    PublishType.ADAPTER: AdapterPublishInfo,
    PublishType.PLUGIN: PluginPublishInfo,
    PublishType.DRIVER: DriverPublishInfo,
}


def validate_info(
    publish_type: PublishType,
    raw_data: dict[str, Any],
    previous_data: list[dict[str, Any]] | None,
) -> ValidationDict:
    """根据发布类型验证数据是否符合规范

    Args:
        publish_type (PublishType): 发布类型
        raw_data (dict[str, Any]): 原始数据
        previous_data (list[dict[str, Any]] | None): 当前商店数据，用于验证数据是否重复
    """
    context = {
        "previous_data": previous_data,
        "valid_data": {},  # 用来存放验证通过的数据
        # 验证过程中可能需要用到的数据
        # 存放在 context 中方便 FieldValidator 使用
        "test_output": raw_data.get("test_output", ""),  # 测试输出
        "skip_test": raw_data.get("skip_test", False),  # 是否跳过测试
    }

    info: PublishInfoModels | None = None
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
        valid_data=context.get("valid_data", {}),
        info=info,
        errors=errors,
    )
