import json

from inline_snapshot import snapshot
from pytest_mock import MockerFixture
from respx import MockRouter


async def test_docker_plugin_test(mocked_api: MockRouter, mocker: MockerFixture):
    from src.providers.docker_test import DockerPluginTest, DockerTestResult

    mocked_run = mocker.Mock()
    mocked_run.return_value = json.dumps(
        {
            "metadata": {},
            "outputs": ["test"],
            "load": True,
            "run": True,
            "version": "0.0.1",
            "config": "",
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
            config="",
            load=True,
            metadata=None,
            outputs=["test"],
            run=True,
            test_env="python==3.12",
            version="0.0.1",
        )
    )

    assert not mocked_api["store_plugins"].called
    mocked_run.assert_called_once_with(
        "ghcr.io/nonebot/nonetest:3.12-latest",
        environment=snapshot(
            {
                "PLUGIN_INFO": "project_link:module_name",
                "PLUGIN_CONFIG": "",
                "PLUGINS_URL": "https://raw.githubusercontent.com/nonebot/registry/results/plugins.json",
            }
        ),
        detach=False,
    )
