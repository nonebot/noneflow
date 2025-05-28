import json

import pytest
from inline_snapshot import snapshot


@pytest.mark.asyncio
async def test_registry_update_payload_bot():
    from src.providers.models import RegistryUpdatePayload, RepoInfo

    payload = json.dumps(
        {
            "repo_info": {
                "owner": "test_owner",
                "repo": "test_repo",
            },
            "artifact_id": 1,
        }
    )

    payload = RegistryUpdatePayload.model_validate_json(payload)
    assert isinstance(payload, RegistryUpdatePayload)
    assert payload == snapshot(
        RegistryUpdatePayload(
            repo_info=RepoInfo(owner="test_owner", repo="test_repo"), artifact_id=1
        )
    )
    registry = payload.get_artifact_data()
    assert registry == snapshot(
        {
            "repo": "test_repo",
            "owner": "test_owner",
            "event_type": "registry_update",
            "client_payload": {
                "repo_info": {"owner": "test_owner", "repo": "test_repo"},
                "artifact_id": 1,
            },
        }
    )


@pytest.mark.asyncio
async def test_registry_update_payload_plugin():
    from src.providers.models import RegistryUpdatePayload, RepoInfo

    payload = json.dumps(
        {
            "repo_info": {
                "owner": "test_owner",
                "repo": "test_repo",
            },
            "artifact_id": 2,
        }
    )

    payload = RegistryUpdatePayload.model_validate_json(payload)
    assert isinstance(payload, RegistryUpdatePayload)
    assert payload == snapshot(
        RegistryUpdatePayload(
            repo_info=RepoInfo(owner="test_owner", repo="test_repo"), artifact_id=2
        )
    )
    registry = payload.get_artifact_data()
    assert registry == snapshot(
        {
            "repo": "test_repo",
            "owner": "test_owner",
            "event_type": "registry_update",
            "client_payload": {
                "repo_info": {"owner": "test_owner", "repo": "test_repo"},
                "artifact_id": 1,
            },
        }
    )
