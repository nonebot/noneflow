import json
import zipfile
from io import BytesIO

from inline_snapshot import snapshot
from pytest_mock import MockerFixture


async def test_registry_update_payload_bot(mocker: MockerFixture):
    from src.providers.constants import REGISTRY_DATA_NAME
    from src.providers.models import (
        BotPublishInfo,
        Color,
        RegistryArtifactData,
        RegistryUpdatePayload,
        RepoInfo,
        Tag,
    )

    mocked_installation_github = mocker.MagicMock()

    mocked_github = mocker.patch("src.providers.models.GitHub")
    mocked_github().with_auth.return_value = mocked_installation_github

    raw_data = {
        "name": "name",
        "desc": "desc",
        "author": "author",
        "author_id": 1,
        "homepage": "https://nonebot.dev",
        "tags": [Tag(label="test", color=Color("#ffffff"))],
    }
    info = BotPublishInfo.model_construct(**raw_data)
    registry_data = RegistryArtifactData.from_info(info)

    # 创建 zip 文件内容
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 将 registry_data 转换为 JSON 字符串并添加到 zip 中
        json_content = registry_data.model_dump_json(indent=2)
        zip_file.writestr(REGISTRY_DATA_NAME, json_content)

    # 获取 zip 文件的字节内容
    zip_content = zip_buffer.getvalue()

    mocked_artifact = mocker.MagicMock()
    mocked_artifact.content = zip_content

    mocked_installation_github.rest.actions.download_artifact.return_value = (
        mocked_artifact
    )

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
    assert registry.model_dump() == snapshot(
        {
            "store": {
                "name": "name",
                "desc": "desc",
                "author_id": 1,
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            },
            "registry": {
                "name": "name",
                "desc": "desc",
                "author": "author",
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            },
            "store_test_result": None,
        }
    )


async def test_registry_update_payload_plugin(mocker: MockerFixture):
    from src.providers.constants import REGISTRY_DATA_NAME
    from src.providers.models import (
        Color,
        PluginPublishInfo,
        RegistryArtifactData,
        RegistryUpdatePayload,
        RepoInfo,
        Tag,
    )

    mocked_installation_github = mocker.MagicMock()

    mocked_github = mocker.patch("src.providers.models.GitHub")
    mocked_github().with_auth.return_value = mocked_installation_github

    raw_data = {
        "module_name": "module_name",
        "project_link": "project_link",
        "name": "name",
        "desc": "desc",
        "author": "author",
        "author_id": 1,
        "homepage": "https://nonebot.dev",
        "tags": [Tag(label="test", color=Color("#ffffff"))],
        "type": "application",
        "supported_adapters": None,
        "load": True,
        "skip_test": False,
        "test_output": "test_output",
        "version": "0.0.1",
        "metadata": True,
        "time": "2023-10-01T00:00:00Z",
    }
    info = PluginPublishInfo.model_construct(**raw_data)
    registry_data = RegistryArtifactData.from_info(info)

    # 创建 zip 文件内容
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 将 registry_data 转换为 JSON 字符串并添加到 zip 中
        json_content = registry_data.model_dump_json(indent=2)
        zip_file.writestr(REGISTRY_DATA_NAME, json_content)

    # 获取 zip 文件的字节内容
    zip_content = zip_buffer.getvalue()

    mocked_artifact = mocker.MagicMock()
    mocked_artifact.content = zip_content

    mocked_installation_github.rest.actions.download_artifact.return_value = (
        mocked_artifact
    )

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
    assert registry.model_dump() == snapshot(
        {
            "store": {
                "module_name": "module_name",
                "project_link": "project_link",
                "author_id": 1,
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
            },
            "registry": {
                "module_name": "module_name",
                "project_link": "project_link",
                "name": "name",
                "desc": "desc",
                "author": "author",
                "homepage": "https://nonebot.dev",
                "tags": [{"label": "test", "color": "#ffffff"}],
                "is_official": False,
                "type": "application",
                "supported_adapters": None,
                "valid": True,
                "time": "2023-10-01T00:00:00Z",
                "version": "0.0.1",
                "skip_test": False,
            },
            "store_test_result": {
                "time": "2023-08-23T09:22:14.836035+08:00",
                "config": "",
                "version": "0.0.1",
                "test_env": {"python==3.12": True},
                "results": {"validation": True, "load": True, "metadata": True},
                "outputs": {
                    "validation": None,
                    "load": "test_output",
                    "metadata": {
                        "name": "name",
                        "description": "desc",
                        "homepage": "https://nonebot.dev",
                        "type": "application",
                        "supported_adapters": None,
                    },
                },
            },
        }
    )
