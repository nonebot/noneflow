"""插件加载测试

测试代码修改自 <https://github.com/Lancercmd/nonebot2-store-test>，谢谢 [Lan 佬](https://github.com/Lancercmd)。
"""
# ruff: noqa: T201, ASYNC109

import asyncio
import json
import os
import re
from asyncio import create_subprocess_shell, subprocess
from pathlib import Path

import httpx

from src.providers.constants import REGISTRY_PLUGINS_URL

from .render import render_fake, render_runner


def strip_ansi(text: str | None) -> str:
    """去除 ANSI 转义字符"""
    if not text:
        return ""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def get_plugin_list() -> dict[str, str]:
    """获取插件列表

    通过 package_name 获取 module_name
    """
    plugins = httpx.get(REGISTRY_PLUGINS_URL).json()

    return {
        canonicalize_name(plugin["project_link"]): plugin["module_name"]
        for plugin in plugins
    }


_canonicalize_regex = re.compile(r"[-_.]+")


def canonicalize_name(name: str) -> str:
    """规范化名称

    packaging.utils 中的 canonicalize_name 实现
    """
    return _canonicalize_regex.sub("-", name).lower()


def extract_version(output: str, project_link: str) -> str | None:
    """提取插件版本"""
    output = strip_ansi(output)

    # 匹配 poetry show 的输出
    match = re.search(r"version\s+:\s+(\S+)", output)
    if match:
        return match.group(1).strip()

    # poetry 使用 packaging.utils 中的 canonicalize_name 规范化名称
    # 在这里我们也需要规范化名称，以正确匹配版本号
    project_link = canonicalize_name(project_link)

    # 匹配版本解析失败的情况
    match = re.search(
        rf"depends on {project_link} \(\^(\S+)\), version solving failed\.", output
    )
    if match:
        return match.group(1).strip()

    # 插件安装失败的情况
    match = re.search(rf"Using version \^(\S+) for {project_link}", output)
    if match:
        return match.group(1).strip()

    match = re.search(rf"- Installing {project_link} \((\S+)\)", output)
    if match:
        return match.group(1).strip()


def parse_requirements(requirements: str) -> dict[str, str]:
    """解析 requirements.txt 文件"""
    # anyio==3.6.2 ; python_version >= "3.11" and python_version < "4.0"
    # pydantic[dotenv]==1.10.6 ; python_version >= "3.10" and python_version < "4.0"
    results = {}
    for line in requirements.strip().splitlines():
        match = re.match(r"^(.+?)(?:\[.+\])?==(.+) ;", line)
        if match:
            package_name = match.group(1)
            version = match.group(2)
            results[package_name] = version
    return results


class PluginTest:
    def __init__(
        self,
        python_version: str,
        project_link: str,
        module_name: str,
        config: str | None = None,
    ) -> None:
        """插件测试构造函数

        Args:
            project_info (str): 项目信息，格式为 project_link:module_name
            config (str | None, optional): 插件配置. 默认为 None.
        """
        self.python_version = python_version

        self.project_link = project_link
        self.module_name = module_name
        self.config = config

        self._plugin_list = None
        self._test_dir = Path("plugin_test")
        # 插件信息
        self._version = None
        # 插件测试结果
        self._create = False
        self._run = False
        # 插件输出
        self._lines_output = []
        # 插件测试环境
        self._deps = []
        self._test_env = []
        self._test_python_version = "unknown"

    @property
    def key(self) -> str:
        """插件的标识符

        project_link:module_name
        例：nonebot-plugin-test:nonebot_plugin_test
        """
        return f"{self.project_link}:{self.module_name}"

    @property
    def env(self) -> dict[str, str]:
        """获取环境变量"""
        env = os.environ.copy()
        # 删除虚拟环境变量，防止 poetry 使用运行当前脚本的虚拟环境
        env.pop("VIRTUAL_ENV", None)
        # 启用 LOGURU 的颜色输出
        env["LOGURU_COLORIZE"] = "true"
        # Poetry 配置
        # https://python-poetry.org/docs/configuration/#virtualenvsin-project
        env["POETRY_VIRTUALENVS_IN_PROJECT"] = "true"
        # https://python-poetry.org/docs/configuration/#virtualenvsprefer-active-python-experimental
        env["POETRY_VIRTUALENVS_PREFER_ACTIVE_PYTHON"] = "true"
        return env

    def _log_output(self, msg: str):
        # print(msg)
        self._lines_output.append(msg)

    async def run(self):
        """插件测试入口"""
        # 创建插件测试项目
        await self.create_poetry_project()
        if self._create:
            await asyncio.gather(
                self.show_package_info(),
                self.show_plugin_dependencies(),
                self.get_python_version(),
            )
            await self.run_poetry_project()

        # 补上获取到 Python 版本
        self._test_env.insert(0, f"python=={self._test_python_version}")
        # 读取插件元数据
        metadata = None
        metadata_path = self._test_dir / "metadata.json"
        if metadata_path.exists():
            with open(self._test_dir / "metadata.json", encoding="utf-8") as f:
                metadata = json.load(f)

        result = {
            "metadata": metadata,
            "output": "\n".join(self._lines_output),
            "load": self._run,
            "run": self._create,
            "version": self._version,
            "config": self.config,
            "test_env": " ".join(self._test_env),
        }
        # 输出测试结果
        print(json.dumps(result, ensure_ascii=False))
        return result

    async def command(self, cmd: str, timeout: int = 300) -> tuple[bool, str, str]:
        """执行命令

        Args:
            cmd (str): 命令
            timeout (int, optional): 超时限制. Defaults to 300.

        Returns:
            tuple[bool, str, str]: 命令执行返回值，标准输出，标准错误
        """
        proc = await create_subprocess_shell(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self._test_dir,
            env=self.env,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
            code = proc.returncode
        except TimeoutError:
            proc.terminate()
            # 超时后仍需读取 stdout 与 stderr 的内容
            stdout = "执行命令超时\n".encode()
            stdout += await proc.stdout.read() if proc.stdout else b""
            stderr = await proc.stderr.read() if proc.stderr else b""
            code = 1

        return not code, stdout.decode(), stderr.decode()

    async def create_poetry_project(self):
        """创建 poetry 项目用来测试插件"""
        if not self._test_dir.exists():
            self._test_dir.mkdir()

            code, stdout, stderr = await self.command(
                f"""uv venv --python {self.python_version} && poetry init -n --python "~{self.python_version}" && poetry env info --ansi && poetry add {self.project_link}"""
            )

            self._create = code

            if self._create:
                self._log_output(f"项目 {self.project_link} 创建成功。")
                self._std_output(stdout)
            else:
                # 创建失败时尝试从报错中获取插件版本号
                self._version = extract_version(stdout + stderr, self.project_link)

                self._log_output(f"项目 {self.project_link} 创建失败：")
                self._std_output(stdout, stderr)

        else:
            self._log_output(f"项目 {self.project_link} 已存在，跳过创建。")
            self._create = True

    async def show_package_info(self) -> None:
        """获取插件的版本与插件信息"""
        if self._test_dir.exists():
            code, stdout, stderr = await self.command(
                f"poetry show {self.project_link}"
            )
            if code:
                # 获取插件版本
                self._version = extract_version(stdout, self.project_link)

                # 记录插件信息至输出
                self._log_output(f"插件 {self.project_link} 的信息如下：")
                self._std_output(stdout)
            else:
                self._log_output(f"插件 {self.project_link} 信息获取失败。")
                self._std_output(stdout, stderr)

    async def run_poetry_project(self) -> None:
        """运行插件"""
        if self._test_dir.exists():
            # 默认使用 fake 驱动
            with open(self._test_dir / ".env", "w", encoding="utf-8") as f:
                f.write("DRIVER=fake")
            # 如果提供了插件配置项，则写入配置文件
            if self.config is not None:
                with open(self._test_dir / ".env.prod", "w", encoding="utf-8") as f:
                    f.write(self.config)

            fake_script = await render_fake()
            with open(self._test_dir / "fake.py", "w", encoding="utf-8") as f:
                f.write(fake_script)

            runner_script = await render_runner(self.module_name, self._deps)
            with open(self._test_dir / "runner.py", "w", encoding="utf-8") as f:
                f.write(runner_script)

            code, stdout, stderr = await self.command(
                "poetry run python runner.py", timeout=600
            )

            self._run = code

            if self._run:
                self._log_output(f"插件 {self.module_name} 加载正常：")
                self._std_output(stdout)
            else:
                self._log_output(f"插件 {self.module_name} 加载出错：")
                self._std_output(stdout, stderr)

    async def show_plugin_dependencies(self) -> None:
        """获取插件的依赖"""
        if self._test_dir.exists():
            code, stdout, stderr = await self.command("poetry export --without-hashes")

            if code:
                self._log_output(f"插件 {self.project_link} 依赖的插件如下：")
                requirements = parse_requirements(stdout)
                self._deps = self._get_deps(requirements)
                self._test_env = self._get_test_env(requirements)
                self._log_output(f"    {', '.join(self._deps)}")
            else:
                self._log_output(f"插件 {self.project_link} 依赖获取失败。")
                self._std_output(stdout, stderr)

    async def get_python_version(self):
        """获取 Python 版本"""
        if self._test_dir.exists():
            code, stdout, stderr = await self.command("poetry run python --version")
            if code:
                version = stdout.strip()
                if version.startswith("Python "):
                    self._test_python_version = version.removeprefix("Python ")
            else:
                self._log_output("Python 版本获取失败。")
                self._std_output(stdout, stderr)

    @property
    def plugin_list(self) -> dict[str, str]:
        """获取插件列表"""
        if self._plugin_list is None:
            self._plugin_list = get_plugin_list()
        return self._plugin_list

    def _std_output(self, stdout: str, stderr: str = ""):
        """将标准输出流与标准错误流记录并输出"""
        _out = stdout.strip().splitlines()
        _err = stderr.strip().splitlines()

        for i in _out:
            self._log_output(f"    {i}")
        for i in _err:
            self._log_output(f"    {i}")

    def _get_deps(self, requirements: dict[str, str]) -> list[str]:
        """获取插件依赖"""
        deps = []
        for package_name in requirements:
            if (
                package_name in self.plugin_list
                # 不用包括插件自己
                and package_name != canonicalize_name(self.project_link)
            ):
                module_name = self.plugin_list[package_name]
                deps.append(module_name)
        return deps

    def _get_test_env(self, requirements: dict[str, str]) -> list[str]:
        """获取测试环境"""
        envs = []
        # 特定插件依赖
        # 当前仅需记录 nonebot2 和 pydantic 的版本
        if "nonebot2" in requirements:
            envs.append(f"nonebot2=={requirements['nonebot2']}")
        if "pydantic" in requirements:
            envs.append(f"pydantic=={requirements['pydantic']}")
        return envs
