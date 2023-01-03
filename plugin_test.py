""" 插件加载测试 

主要测试代码来自 https://github.com/Lancercmd/nonebot2-store-test
"""

import json
import os
import re
from asyncio import create_subprocess_shell, run, subprocess
from pathlib import Path
from typing import List

# 匹配信息的正则表达式
ISSUE_PATTERN = r"\*\*{}：\*\*\s+([^\s*].*?)(?=(?:\s+\*\*|$))"
# 插件信息
PROJECT_LINK_PATTERN = re.compile(ISSUE_PATTERN.format("PyPI 项目名"))
MODULE_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("插件 import 包名"))

RUNNER = """from nonebot import init, load_plugin

init()
valid = load_plugin("{}")
if not valid:
    exit(1)
else:
    exit(0)
"""


class PluginTest:
    def __init__(self, project_link: str, module_name: str) -> None:
        self._path = Path("plugin_test")

        self.project_link = project_link
        self.module_name = module_name

        self._create = False
        self._run = False

        self._output_lines: List[str] = []

    async def run(self):
        await self.create_poetry_project()
        if self._create:
            await self.show_package_info()
            await self.run_poetry_project()

        # 输出测试结果
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"RESULT={self._run}\n")
        # 输出测试输出
        output = "\n".join(self._output_lines)
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"OUTPUT<<EOF\n{output}\nEOF\n")

    async def create_poetry_project(self) -> None:
        if not self._path.exists():
            proc = await create_subprocess_shell(
                f"poetry new {self._path.resolve()} && cd {self._path.resolve()} && poetry add {self.project_link} && poetry run python -m pip install -U pip {self.project_link}",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _, stderr = await proc.communicate()

            self._create = not "ERROR" in stderr.decode()
            if self._create:
                print(f"项目 {self.project_link} 创建成功。")
            else:
                self.log_output(f"项目 {self.project_link} 创建失败：")
                for i in stderr.decode().strip().splitlines():
                    self.log_output(f"    {i}")
        else:
            self.log_output(f"项目 {self.project_link} 已存在，跳过创建。")
            self._create = True

    async def show_package_info(self) -> None:
        if self._path.exists():
            proc = await create_subprocess_shell(
                f"cd {self._path.resolve()} && poetry show {self.project_link}",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            code = proc.returncode
            if not code:
                self.log_output(f"插件 {self.project_link} 的信息如下：")
                for i in stdout.decode().strip().splitlines():
                    self.log_output(f"    {i}")
            else:
                self.log_output(f"插件 {self.project_link} 信息获取失败。")

    async def run_poetry_project(self) -> None:
        if self._path.exists():
            with open(self._path / "runner.py", "w") as f:
                f.write(RUNNER.format(self.module_name))

            proc = await create_subprocess_shell(
                f"cd {self._path.resolve()} && poetry run python runner.py",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            code = proc.returncode

            self._run = not code
            if self._run:
                self.log_output(f"插件 {self.module_name} 加载正常。")
            else:
                self.log_output(f"插件 {self.module_name} 加载出错：")
                _err = stderr.decode().strip()
                if len(_err.splitlines()) > 1:
                    for i in _err.splitlines():
                        self.log_output(f"    {i}")
                elif not _err:
                    self.log_output(stdout.decode().strip())
                else:
                    self.log_output(_err)

    def log_output(self, output: str) -> None:
        """记录输出，同时打印到控制台"""
        print(output)
        self._output_lines.append(output)


def main():
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        print("未找到 GITHUB_EVENT_PATH，已跳过")
        return

    with open(event_path) as f:
        event = json.load(f)

    event_name = os.environ.get("GITHUB_EVENT_NAME")
    if event_name not in ["issues", "issue_comment"]:
        print(f"不支持的事件: {event_name}，已跳过")
        return

    issue = event["issue"]

    pull_request = issue.get("pull_request")
    if pull_request:
        print("评论在拉取请求下，已跳过")
        return

    state = issue.get("state")
    if state != "open":
        print("议题未开启，已跳过")
        return

    title = issue.get("title")
    if not title.startswith("Plugin"):
        print("议题与插件发布无关，已跳过")
        return

    issue_body = issue.get("body")
    project_link = PROJECT_LINK_PATTERN.search(issue_body)
    module_name = MODULE_NAME_PATTERN.search(issue_body)

    if not project_link or not module_name:
        print("议题中没有插件信息，已跳过")
        return

    # 测试插件
    test = PluginTest(project_link.group(1), module_name.group(1))
    run(test.run())


if __name__ == "__main__":
    main()
