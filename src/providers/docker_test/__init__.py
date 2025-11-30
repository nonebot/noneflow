import json
import traceback
from typing import TypedDict

import docker
from pydantic import BaseModel, SkipValidation, field_validator

from src.providers.constants import (
    DOCKER_BIND_RESULT_PATH,
    DOCKER_IMAGES,
    PLUGIN_TEST_DIR,
    PYPI_KEY_TEMPLATE,
)
from src.providers.utils import pypi_key_to_path


class Metadata(TypedDict):
    """插件元数据"""

    name: str
    desc: str
    homepage: str | None
    type: str | None
    supported_adapters: list[str] | None


class DockerTestResult(BaseModel):
    """Docker 测试结果"""

    run: bool
    """ 是否运行测试 """
    load: bool
    """ 是否加载成功 """
    output: str
    """ 测试输出 """
    version: str | None = None
    """ 测试版本 """
    config: str = ""
    """ 测试配置 """
    test_env: str = ""
    """测试环境

    python==3.12 nonebot2==2.4.0 pydantic==2.10.0
    """
    metadata: SkipValidation[Metadata] | None = None
    """ 插件元数据 """

    @field_validator("config", mode="before")
    @classmethod
    def config_validator(cls, v: str | None):
        return v or ""


class DockerPluginTest:
    def __init__(self, project_link: str, module_name: str, config: str = ""):
        self.project_link = project_link
        self.module_name = module_name
        self.config = config

        if not PLUGIN_TEST_DIR.exists():
            PLUGIN_TEST_DIR.mkdir(parents=True, exist_ok=True)

    async def run(self, version: str) -> DockerTestResult:
        """运行 Docker 容器测试插件

        Args:
            version (str): 对应的 Python 版本

        Returns:
            DockerTestResult: 测试结果
        """
        # 连接 Docker 环境
        client = docker.DockerClient(base_url="unix://var/run/docker.sock")
        key = PYPI_KEY_TEMPLATE.format(
            project_link=self.project_link, module_name=self.module_name
        )
        plugin_test_result = PLUGIN_TEST_DIR / f"{pypi_key_to_path(key)}.json"

        # 创建文件，以确保 Docker 容器内可以写入
        plugin_test_result.touch(exist_ok=True)

        try:
            # 运行 Docker 容器，捕获输出。 容器内运行的代码拥有超时设限，此处无需设置超时
            output = client.containers.run(
                DOCKER_IMAGES,
                environment={
                    # 运行测试的 Python 版本
                    "PYTHON_VERSION": version,
                    # 插件信息
                    "PROJECT_LINK": self.project_link,
                    "MODULE_NAME": self.module_name,
                    "PLUGIN_CONFIG": self.config,
                },
                detach=False,
                remove=True,
                volumes={
                    plugin_test_result.resolve(strict=False).as_posix(): {
                        "bind": DOCKER_BIND_RESULT_PATH,
                        "mode": "rw",
                    }
                },
            )

            try:
                # 若测试结果文件存在且可解析，则优先使用测试结果文件
                data = json.loads(plugin_test_result.read_text(encoding="utf-8"))
            except Exception as e:
                # 如果测试结果文件不存在或不可解析，则尝试使用容器输出内容
                # 这个时候才需要解码容器输出内容，避免不必要的解码开销
                try:
                    data = json.loads(output.decode(encoding="utf-8"))
                except json.JSONDecodeError:
                    data = {
                        "run": True,
                        "load": False,
                        "output": f"""
                        测试结果文件解析失败，输出内容写入失败。
                        {e}
                        输出内容：{output}
                        """,
                    }
        except Exception as e:
            # 格式化异常堆栈信息
            trackback = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            MAX_OUTPUT = 2000
            if len(trackback) > MAX_OUTPUT:
                trackback = trackback[-MAX_OUTPUT:]

            data = {
                "run": False,
                "load": False,
                "output": trackback,
            }
        return DockerTestResult(**data)
