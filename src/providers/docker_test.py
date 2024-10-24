import json

import docker
from src.providers.constants import DOCKER_IMAGES
from src.providers.store_test.models import DockerTestResult


class DockerPluginTest:
    def __init__(
        self, docker_images: str, project_link: str, module_name: str, config: str = ""
    ):
        self.docker_images = docker_images
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
            dict[str, Any]: 测试结果
        """
        image_name = DOCKER_IMAGES.format(version)
        # 连接 Docker 环境
        client = docker.DockerClient(base_url="unix://var/run/docker.sock")

        # 运行 Docker 容器，捕获输出。 容器内运行的代码拥有超时设限，此处无需设置超时
        output = client.containers.run(
            image_name,
            environment={"PLUGIN_INFO": self.key, "PLUGIN_CONFIG": self.config},
            detach=False,
        ).decode()

        data = json.loads(output)
        data["test_env"] = f"python=={version}"
        return DockerTestResult(**data)
