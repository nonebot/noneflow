import json
from pathlib import Path

from inline_snapshot import snapshot
from pytest_mock import MockerFixture
from respx import MockRouter


async def test_docker_plugin_test_from_file(
    mocked_api: MockRouter,
    mocker: MockerFixture,
    tmp_path: Path,
):
    from src.providers.constants import DOCKER_BIND_RESULT_PATH
    from src.providers.docker_test import DockerPluginTest, DockerTestResult

    mocker.patch("src.providers.docker_test.PLUGIN_TEST_DIR", tmp_path)
    test_result_path = tmp_path / "project-link-module-name.json"

    data = json.dumps(
        {
            "metadata": None,
            "output": "test",
            "load": True,
            "run": True,
            "version": "0.0.1",
            "config": "",
            "test_env": "python==3.12",
        }
    )

    with open(test_result_path, "w", encoding="utf-8") as f:
        f.write(data)

    mocked_run = mocker.Mock()
    mocked_run.return_value = b""
    mocked_client = mocker.Mock()
    mocked_client.containers.run = mocked_run
    mocked_docker = mocker.patch("docker.DockerClient")
    mocked_docker.return_value = mocked_client

    test = DockerPluginTest("project_link", "module_name")
    result = await test.run("3.12")

    assert result == snapshot(
        DockerTestResult(
            run=True, load=True, output="test", version="0.0.1", test_env="python==3.12"
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
        volumes={
            test_result_path.resolve(strict=False).as_posix(): {
                "bind": DOCKER_BIND_RESULT_PATH,
                "mode": "rw",
            }
        },
    )


async def test_docker_plugin_test_from_file_invalid_output(
    mocked_api: MockRouter,
    mocker: MockerFixture,
    tmp_path: Path,
):
    """测试结果文件内容不是合法的 UTF-8 编码

    不会影响到测试结果的读取，仍然会从文件中读取结果
    """
    from src.providers.constants import DOCKER_BIND_RESULT_PATH
    from src.providers.docker_test import DockerPluginTest, DockerTestResult

    mocker.patch("src.providers.docker_test.PLUGIN_TEST_DIR", tmp_path)
    test_result_path = tmp_path / "project-link-module-name.json"

    data = json.dumps(
        {
            "metadata": None,
            "output": "test",
            "load": True,
            "run": True,
            "version": "0.0.1",
            "config": "",
            "test_env": "python==3.12",
        }
    )

    with open(test_result_path, "w", encoding="utf-8") as f:
        f.write(data)

    mocked_run = mocker.Mock()
    # 非法 UTF-8 编码
    mocked_run.return_value = b"\xff\xfe\xfd"
    mocked_client = mocker.Mock()
    mocked_client.containers.run = mocked_run
    mocked_docker = mocker.patch("docker.DockerClient")
    mocked_docker.return_value = mocked_client

    test = DockerPluginTest("project_link", "module_name")
    result = await test.run("3.12")

    assert result == snapshot(
        DockerTestResult(
            run=True, load=True, output="test", version="0.0.1", test_env="python==3.12"
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
        volumes={
            test_result_path.resolve(strict=False).as_posix(): {
                "bind": DOCKER_BIND_RESULT_PATH,
                "mode": "rw",
            }
        },
    )


async def test_docker_plugin_test_from_output(
    mocked_api: MockRouter,
    mocker: MockerFixture,
    tmp_path: Path,
):
    from src.providers.constants import DOCKER_BIND_RESULT_PATH
    from src.providers.docker_test import DockerPluginTest, DockerTestResult

    mocker.patch("src.providers.docker_test.PLUGIN_TEST_DIR", tmp_path)
    test_result_path = tmp_path / "project-link-module-name.json"

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
    ).encode(encoding="utf-8")
    mocked_client = mocker.Mock()
    mocked_client.containers.run = mocked_run
    mocked_docker = mocker.patch("docker.DockerClient")
    mocked_docker.return_value = mocked_client

    test = DockerPluginTest("project_link", "module_name")
    result = await test.run("3.12")

    assert result == snapshot(
        DockerTestResult(
            load=True, output="test", run=True, version="0.0.1", test_env="python==3.12"
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
        volumes={
            test_result_path.resolve(strict=False).as_posix(): {
                "bind": DOCKER_BIND_RESULT_PATH,
                "mode": "rw",
            }
        },
    )


async def test_docker_plugin_test_exception(
    mocked_api: MockRouter,
    mocker: MockerFixture,
    tmp_path: Path,
):
    """插件测试时报错"""
    from src.providers.constants import DOCKER_BIND_RESULT_PATH
    from src.providers.docker_test import DockerPluginTest

    mocker.patch("src.providers.docker_test.PLUGIN_TEST_DIR", tmp_path)
    test_result_path = tmp_path / "project-link-module-name.json"

    mocked_run = mocker.Mock()
    mocked_run.side_effect = Exception("Docker failed")
    mocked_client = mocker.Mock()
    mocked_client.containers.run = mocked_run
    mocked_docker = mocker.patch("docker.DockerClient")
    mocked_docker.return_value = mocked_client

    test = DockerPluginTest("project_link", "module_name")
    result = await test.run("3.12")

    assert result.output.endswith("Exception: Docker failed\n")

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
        volumes={
            test_result_path.resolve(strict=False).as_posix(): {
                "bind": DOCKER_BIND_RESULT_PATH,
                "mode": "rw",
            }
        },
    )


async def test_docker_plugin_test_metadata_some_fields_empty(
    mocked_api: MockRouter,
    mocker: MockerFixture,
    tmp_path: Path,
):
    """测试 metadata 的部分字段为空"""
    from src.providers.constants import DOCKER_BIND_RESULT_PATH
    from src.providers.docker_test import DockerPluginTest, DockerTestResult

    mocker.patch("src.providers.docker_test.PLUGIN_TEST_DIR", tmp_path)
    test_result_path = tmp_path / "project-link-module-name.json"

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
            output="test",
            run=True,
            version="0.0.1",
            test_env="python==3.12",
            metadata={
                "name": "name",
                "desc": "desc",
                "homepage": None,
                "type": None,
                "supported_adapters": None,
            },
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
        volumes={
            test_result_path.resolve(strict=False).as_posix(): {
                "bind": DOCKER_BIND_RESULT_PATH,
                "mode": "rw",
            }
        },
    )


async def test_docker_plugin_test_metadata_some_fields_invalid(
    mocked_api: MockRouter,
    mocker: MockerFixture,
    tmp_path: Path,
):
    """测试 metadata 的部分字段不符合规范"""
    from src.providers.constants import DOCKER_BIND_RESULT_PATH
    from src.providers.docker_test import DockerPluginTest, DockerTestResult

    mocker.patch("src.providers.docker_test.PLUGIN_TEST_DIR", tmp_path)
    test_result_path = tmp_path / "project-link-module-name.json"

    mocked_run = mocker.Mock()
    mocked_run.return_value = b""
    mocked_client = mocker.Mock()
    mocked_client.containers.run = mocked_run
    mocked_docker = mocker.patch("docker.DockerClient")
    mocked_docker.return_value = mocked_client

    with open(test_result_path, "w", encoding="utf-8") as f:
        json.dump(
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
            },
            f,
        )

    test = DockerPluginTest("project_link", "module_name")
    result = await test.run("3.12")

    assert result == snapshot(
        DockerTestResult(
            run=True,
            load=True,
            output="test",
            version="0.0.1",
            test_env="python==3.12",
            metadata={  # type: ignore
                "name": "name",
                "desc": "desc",
                "homepage": 12,
                "type": True,
                "supported_adapters": {},
            },
        )
    )

    assert not mocked_api["store_plugins"].called
    mocked_run.assert_called_once_with(
        "ghcr.io/nonebot/nonetest:latest",
        environment={
            "PROJECT_LINK": "project_link",
            "MODULE_NAME": "module_name",
            "PLUGIN_CONFIG": "",
            "PYTHON_VERSION": "3.12",
        },
        detach=False,
        remove=True,
        volumes={
            test_result_path.resolve(strict=False).as_posix(): {
                "bind": DOCKER_BIND_RESULT_PATH,
                "mode": "rw",
            }
        },
    )
