import json
from typing import TypedDict

import docker
from pydantic import BaseModel, SkipValidation, field_validator

from src.providers.constants import DOCKER_IMAGES


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

    async def run(self, version: str) -> DockerTestResult:
        """运行 Docker 容器测试插件

        Args:
            version (str): 对应的 Python 版本

        Returns:
            DockerTestResult: 测试结果
        """
        # 连接 Docker 环境
        client = docker.DockerClient(base_url="unix://var/run/docker.sock")

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
            ).decode()

            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                data = {
                    "run": True,
                    "load": False,
                    "output": f"插件测试结果解析失败，输出内容非 JSON 格式。{output}",
                }
        except Exception as e:
            data = {
                "run": False,
                "load": False,
                "output": str(e),
            }
        return DockerTestResult(**data)
