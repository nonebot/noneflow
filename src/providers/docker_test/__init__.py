import json
from typing import Any

import docker
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError
from pyjson5 import Json5DecoderException

from src.providers.constants import DOCKER_IMAGES, REGISTRY_PLUGINS_URL
from src.providers.utils import load_json


class Metadata(BaseModel):
    """插件元数据"""

    name: str
    desc: str
    homepage: str
    type: str | None = None
    supported_adapters: list[str] | None = None

    @model_validator(mode="before")
    @classmethod
    def model_validator(cls, data: dict[str, Any]):
        if data.get("desc") is None:
            data["desc"] = data.get("description")
        return data

    @field_validator("supported_adapters", mode="before")
    @classmethod
    def supported_adapters_validator(cls, v: list[str] | str | None):
        if isinstance(v, str):
            try:
                v = load_json(v)
            except Json5DecoderException:
                raise PydanticCustomError("json_type", "JSON 格式不合法")

        return v


class DockerTestResult(BaseModel):
    """Docker 测试结果"""

    run: bool  # 是否运行
    load: bool  # 是否加载成功
    version: str | None = None
    config: str = ""
    # 测试环境 python==3.10 pytest==6.2.5 nonebot2==2.0.0a1 ...
    test_env: str = Field(default="unknown")
    metadata: Metadata | None
    outputs: list[str]

    @field_validator("metadata", mode="before")
    @classmethod
    def metadata_validator(cls, v: Any):
        if v:
            return v
        return None

    @field_validator("config", mode="before")
    @classmethod
    def config_validator(cls, v: str | None):
        return v or ""


class DockerPluginTest:
    def __init__(self, project_link: str, module_name: str, config: str = ""):
        self.project_link = project_link
        self.module_name = module_name
        self.config = config

    @property
    def key(self) -> str:
        """插件的标识符

        project_link:module_name
        例：nonebot-plugin-test:nonebot_plugin_test
        """
        return f"{self.project_link}:{self.module_name}"

    async def run(self, version: str) -> DockerTestResult:
        """运行 Docker 容器测试插件

        Args:
            version (str): 对应的 Python 版本

        Returns:
            DockerTestResult: 测试结果
        """
        image_name = DOCKER_IMAGES.format(version)
        # 连接 Docker 环境
        client = docker.DockerClient(base_url="unix://var/run/docker.sock")

        # 运行 Docker 容器，捕获输出。 容器内运行的代码拥有超时设限，此处无需设置超时
        output = client.containers.run(
            image_name,
            environment={
                "PLUGIN_INFO": self.key,
                "PLUGIN_CONFIG": self.config,
                # 插件测试需要用到的插件列表来验证插件依赖是否正确加载
                "PLUGINS_URL": REGISTRY_PLUGINS_URL,
            },
            detach=False,
            remove=True,
        ).decode()

        data = json.loads(output)
        data["test_env"] = f"python=={version}"
        return DockerTestResult(**data)
