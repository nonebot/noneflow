import json

from inline_snapshot import snapshot
from pytest_mock import MockerFixture
from respx import MockRouter


async def test_docker_plugin_test(mocked_api: MockRouter, mocker: MockerFixture):
    from src.providers.docker_test import DockerPluginTest, DockerTestResult

    mocked_run = mocker.Mock()
    mocked_run.return_value = json.dumps(
        {
            "metadata": None,
            "output": "test",
            "load": True,
            "run": True,
            "version": "0.0.1",
            "config": "",
            "test_env": "python==3.12",
        }
    ).encode()
    mocked_client = mocker.Mock()
    mocked_client.containers.run = mocked_run
    mocked_docker = mocker.patch("docker.DockerClient")
    mocked_docker.return_value = mocked_client

    test = DockerPluginTest("project_link", "module_name")
    result = await test.run("3.12")

    assert result == snapshot(
        DockerTestResult(
            load=True,
            output="test",
            run=True,
            test_env="python==3.12",
            version="0.0.1",
        )
    )

    assert not mocked_api["store_plugins"].called
    mocked_run.assert_called_once_with(
        "ghcr.io/nonebot/nonetest:latest",
        environment=snapshot(
            {
                "PROJECT_LINK": "project_link",
                "MODULE_NAME": "module_name",
                "PLUGIN_CONFIG": "",
                "PYTHON_VERSION": "3.12",
            }
        ),
        detach=False,
        remove=True,
    )


async def test_docker_plugin_test_exception(
    mocked_api: MockRouter, mocker: MockerFixture
):
    """插件测试时报错"""
    from src.providers.docker_test import DockerPluginTest, DockerTestResult

    mocked_run = mocker.Mock()
    mocked_run.side_effect = Exception("Docker failed")
    mocked_client = mocker.Mock()
    mocked_client.containers.run = mocked_run
    mocked_docker = mocker.patch("docker.DockerClient")
    mocked_docker.return_value = mocked_client

    test = DockerPluginTest("project_link", "module_name")
    result = await test.run("3.12")

    assert result == snapshot(
        DockerTestResult(
            run=False,
            load=False,
            output="Docker failed",
        )
    )

    assert not mocked_api["store_plugins"].called
    mocked_run.assert_called_once_with(
        "ghcr.io/nonebot/nonetest:latest",
        environment=snapshot(
            {
                "PROJECT_LINK": "project_link",
                "MODULE_NAME": "module_name",
                "PLUGIN_CONFIG": "",
                "PYTHON_VERSION": "3.12",
            }
        ),
        detach=False,
        remove=True,
    )


async def test_docker_plugin_test_metadata_some_fields_empty(
    mocked_api: MockRouter, mocker: MockerFixture
):
    """测试 metadata 的部分字段为空"""
    from src.providers.docker_test import DockerPluginTest, DockerTestResult

    mocked_run = mocker.Mock()
    mocked_run.return_value = json.dumps(
        {
            "metadata": {
                "name": "name",
                "desc": "desc",
                "homepage": None,
                "type": None,
                "supported_adapters": None,
            },
            "output": "test",
            "load": True,
            "run": True,
            "version": "0.0.1",
            "config": "",
            "test_env": "python==3.12",
        }
    ).encode()
    mocked_client = mocker.Mock()
    mocked_client.containers.run = mocked_run
    mocked_docker = mocker.patch("docker.DockerClient")
    mocked_docker.return_value = mocked_client

    test = DockerPluginTest("project_link", "module_name")
    result = await test.run("3.12")

    assert result == snapshot(
        DockerTestResult(
            load=True,
            metadata={
                "name": "name",
                "desc": "desc",
                "homepage": None,
                "type": None,
                "supported_adapters": None,
            },
            output="test",
            run=True,
            test_env="python==3.12",
            version="0.0.1",
        )
    )

    assert not mocked_api["store_plugins"].called
    mocked_run.assert_called_once_with(
        "ghcr.io/nonebot/nonetest:latest",
        environment=snapshot(
            {
                "PROJECT_LINK": "project_link",
                "MODULE_NAME": "module_name",
                "PLUGIN_CONFIG": "",
                "PYTHON_VERSION": "3.12",
            }
        ),
        detach=False,
        remove=True,
    )


async def test_docker_plugin_test_metadata_some_fields_invalid(
    mocked_api: MockRouter, mocker: MockerFixture
):
    """测试 metadata 的部分字段不符合规范"""
    from src.providers.docker_test import DockerPluginTest, DockerTestResult

    mocked_run = mocker.Mock()
    mocked_run.return_value = json.dumps(
        {
            "metadata": {
                "name": "name",
                "desc": "desc",
                "homepage": 12,
                "type": True,
                "supported_adapters": {},
            },
            "output": "test",
            "load": True,
            "run": True,
            "version": "0.0.1",
            "config": "",
            "test_env": "python==3.12",
        }
    ).encode()
    mocked_client = mocker.Mock()
    mocked_client.containers.run = mocked_run
    mocked_docker = mocker.patch("docker.DockerClient")
    mocked_docker.return_value = mocked_client

    test = DockerPluginTest("project_link", "module_name")
    result = await test.run("3.12")

    assert result == snapshot(
        DockerTestResult(
            load=True,
            metadata={
                "name": "name",
                "desc": "desc",
                "homepage": 12,
                "type": True,
                "supported_adapters": {},
            },  # type: ignore
            output="test",
            run=True,
            test_env="python==3.12",
            version="0.0.1",
        )
    )

    assert not mocked_api["store_plugins"].called
    mocked_run.assert_called_once_with(
        "ghcr.io/nonebot/nonetest:latest",
        environment=snapshot(
            {
                "PROJECT_LINK": "project_link",
                "MODULE_NAME": "module_name",
                "PLUGIN_CONFIG": "",
                "PYTHON_VERSION": "3.12",
            }
        ),
        detach=False,
        remove=True,
    )
