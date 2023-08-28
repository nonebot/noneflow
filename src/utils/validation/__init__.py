""" 验证数据是否符合规范 """

from typing import Any, cast

from pydantic import validate_model

from .models import AdapterPublishInfo, BotPublishInfo, PluginPublishInfo, PublishInfo
from .models import PublishType as PublishType
from .models import Tag
from .models import ValidationDict as ValidationDict
from .utils import color_to_hex

validation_model_map = {
    PublishType.BOT: BotPublishInfo,
    PublishType.ADAPTER: AdapterPublishInfo,
    PublishType.PLUGIN: PluginPublishInfo,
}


def validate_info(
    publish_type: PublishType, raw_data: dict[str, Any]
) -> ValidationDict:
    """验证信息是否符合规范"""
    if publish_type not in validation_model_map:
        raise ValueError("⚠️ 未知的发布类型。")  # pragma: no cover

    data, _, errors = validate_model(validation_model_map[publish_type], raw_data)

    # tags 会被转成 list[Tag]，需要转成 dict
    if "tags" in data:
        tags = cast(list[Tag], data["tags"])
        data["tags"] = [
            {
                "label": tag.label,
                "color": color_to_hex(tag.color),
            }
            for tag in tags
        ]

    # 这个字段仅用于判断是否重复
    # 如果升级至 pydantic 2 后，可以使用 validation-context
    # https://docs.pydantic.dev/latest/usage/validators/#validation-context
    data.pop("previous_data", None)

    errors_with_input = []
    if errors:
        for error in errors.errors():
            error = cast(dict[str, Any], error)
            match error["loc"]:
                case (name,) if isinstance(name, str):
                    # 可能会有字段数据缺失的情况，这种时候不设置 input
                    if name in raw_data:
                        error["input"] = raw_data[name]
                case ("tags", index) if isinstance(index, int):
                    error["input"] = PublishInfo.tags_validator(raw_data["tags"])[index]
                # 标签 list[Tag] 的情况
                case ("tags", index, field) if isinstance(index, int) and isinstance(
                    field, str
                ):
                    tags = PublishInfo.tags_validator(raw_data["tags"])
                    if field in tags[index]:
                        error["input"] = tags[index][field]
                case _:
                    continue
            errors_with_input.append(error)

    # 如果是插件，还需要额外验证插件加载测试结果
    if publish_type == PublishType.PLUGIN:
        skip_plugin_test = raw_data.get("skip_plugin_test")
        plugin_test_result = raw_data.get("plugin_test_result")
        plugin_test_output = raw_data.get("plugin_test_output")
        plugin_test_metadata = raw_data.get("plugin_test_metadata")

        if plugin_test_metadata is None and not skip_plugin_test:
            errors_with_input.append(
                {
                    "loc": ("metadata",),
                    "msg": "无法获取到插件元数据。",
                    "type": "value_error.metadata",
                    "ctx": {"plugin_test_result": plugin_test_result},
                }
            )
            # 如果没有跳过测试且缺少插件元数据，则跳过元数据相关的错误
            # 因为这个时候这些项都会报错，错误在此时没有意义
            metadata_keys = ["name", "desc", "homepage", "type", "supported_adapters"]
            errors_with_input = [
                error
                for error in errors_with_input
                if error["loc"][0] not in metadata_keys
            ]
            # 元数据缺失时，需要删除元数据相关的字段
            for key in metadata_keys:
                data.pop(key, None)

        if not skip_plugin_test and not plugin_test_result:
            errors_with_input.append(
                {
                    "loc": ("plugin_test",),
                    "msg": "插件无法正常加载",
                    "type": "value_error.plugin_test",
                    "ctx": {"output": plugin_test_output},
                }
            )

    return {
        "valid": errors_with_input == [],
        "data": data,
        "errors": errors_with_input,
        # 方便插件使用的数据
        "type": publish_type,
        "name": data.get("name") or raw_data.get("name", ""),
        "author": data.get("author", ""),
    }
