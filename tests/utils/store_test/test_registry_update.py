import json

import pytest
from inline_snapshot import snapshot


@pytest.mark.asyncio
async def test_registry_update_payload_bot():
    from src.providers.models import PublishType, RegistryUpdatePayload

    payload = json.dumps(
        {
            "type": "Bot",
            "registry": {
                "name": "name",
                "desc": "desc",
                "author": "test",
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            },
            "result": None,
        }
    )

    payload = RegistryUpdatePayload.model_validate_json(payload)
    assert isinstance(payload, RegistryUpdatePayload)
    assert payload.type == PublishType.BOT
    assert payload.registry.model_dump() == snapshot(
        {
            "name": "name",
            "desc": "desc",
            "author": "test",
            "homepage": "https://nonebot.dev",
            "tags": [{"label": "test", "color": "#ffffff"}],
            "is_official": False,
        }
    )
    assert payload.result == snapshot(None)


@pytest.mark.asyncio
async def test_registry_update_payload_plugin():
    from src.providers.models import PublishType, RegistryUpdatePayload

    payload = json.dumps(
        {
            "type": "Plugin",
            "registry": {
                "name": "name",
                "desc": "desc",
                "author": "test",
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            },
            "result": None,
        }
    )

    payload = RegistryUpdatePayload.model_validate_json(payload)
    assert isinstance(payload, RegistryUpdatePayload)
    assert payload.type == PublishType.PLUGIN
    assert payload.registry.model_dump() == snapshot(
        {
            "name": "name",
            "desc": "desc",
            "author": "test",
            "homepage": "https://nonebot.dev",
            "tags": [{"label": "test", "color": "#ffffff"}],
            "is_official": False,
        }
    )
    assert payload.result == snapshot(None)
