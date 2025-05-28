import json
import zipfile
from io import BytesIO

from inline_snapshot import snapshot
from pytest_mock import MockerFixture


async def test_registry_update_payload_bot(mocker: MockerFixture):
    from src.providers.constants import REGISTRY_DATA_NAME
    from src.providers.models import (
        Color,
        RegistryArtifactData,
        RegistryBot,
        RegistryUpdatePayload,
        RepoInfo,
        Tag,
    )

    mocked_installation_github = mocker.MagicMock()

    mocked_github = mocker.patch("src.providers.models.GitHub")
    mocked_github().with_auth.return_value = mocked_installation_github

    registry_data = {
        "registry": {
            "name": "test",
            "desc": "desc",
            "author": "test",
            "homepage": "https://nonebot.dev",
            "tags": [{"label": "test", "color": "#ffffff"}],
            "is_official": False,
        },
        "result": None,
    }

    # 创建 zip 文件内容
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 将 registry_data 转换为 JSON 字符串并添加到 zip 中
        json_content = json.dumps(registry_data, indent=2)
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
    assert registry == snapshot(
        RegistryArtifactData(
            registry=RegistryBot(
                name="test",
                desc="desc",
                author="test",
                homepage="https://nonebot.dev",
                tags=[Tag(label="test", color=Color("#ffffff"))],
                is_official=False,
            ),
            result=None,
        )
    )


async def test_registry_update_payload_plugin(mocker: MockerFixture):
    from src.providers.constants import REGISTRY_DATA_NAME
    from src.providers.models import (
        Color,
        RegistryArtifactData,
        RegistryPlugin,
        RegistryUpdatePayload,
        RepoInfo,
        StoreTestResult,
        Tag,
    )

    mocked_installation_github = mocker.MagicMock()

    mocked_github = mocker.patch("src.providers.models.GitHub")
    mocked_github().with_auth.return_value = mocked_installation_github

    registry_data = {
        "registry": {
            "module_name": "module_name",
            "project_link": "project_link",
            "name": "name",
            "desc": "desc",
            "author": "test",
            "homepage": "https://nonebot.dev",
            "tags": [{"label": "test", "color": "#ffffff"}],
            "is_official": False,
            "type": "application",
            "valid": True,
            "time": "2023-09-01T00:00:00.000000Z",
            "version": "1.0.0",
            "skip_test": False,
        },
        "result": {
            "time": "2023-08-23T09:22:14.836035+08:00",
            "config": "log_level=DEBUG",
            "version": "1.0.0",
            "test_env": {"python==3.12": True},
            "results": {"validation": True, "load": True, "metadata": True},
            "outputs": {
                "validation": None,
                "load": "",
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

    # 创建 zip 文件内容
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 将 registry_data 转换为 JSON 字符串并添加到 zip 中
        json_content = json.dumps(registry_data, indent=2)
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
    assert registry == snapshot(
        RegistryArtifactData(
            registry=RegistryPlugin(
                module_name="module_name",
                project_link="project_link",
                name="name",
                desc="desc",
                author="test",
                homepage="https://nonebot.dev",
                tags=[Tag(label="test", color=Color("#ffffff"))],
                is_official=False,
                type="application",
                valid=True,
                time="2023-09-01T00:00:00.000000Z",
                version="1.0.0",
                skip_test=False,
            ),
            result=StoreTestResult(
                config="log_level=DEBUG",
                version="1.0.0",
                test_env={"python==3.12": True},
                results={"validation": True, "load": True, "metadata": True},
                outputs={
                    "validation": None,
                    "load": "",
                    "metadata": {
                        "name": "name",
                        "description": "desc",
                        "homepage": "https://nonebot.dev",
                        "type": "application",
                        "supported_adapters": None,
                    },
                },
            ),
        )
    )
