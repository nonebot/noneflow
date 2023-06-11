""" 插件加载测试 

主要测试代码来自 https://github.com/Lancercmd/nonebot2-store-test
"""

import argparse
import json
import os
import re
from asyncio import create_subprocess_shell, run, subprocess
from pathlib import Path
from urllib.request import urlopen

# GITHUB
GITHUB_OUTPUT_FILE = Path(os.environ.get("GITHUB_OUTPUT", ""))
GITHUB_STEP_SUMMARY_FILE = Path(os.environ.get("GITHUB_STEP_SUMMARY", ""))
# NoneBot Store
STORE_PLUGINS_URL = "https://nonebot.dev/plugins.json"

# 匹配信息的正则表达式
ISSUE_PATTERN = r"### {}\s+([^\s#].*?)(?=(?:\s+###|$))"
# 插件信息
PROJECT_LINK_PATTERN = re.compile(ISSUE_PATTERN.format("PyPI 项目名"))
MODULE_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("插件 import 包名"))
CONFIG_PATTERN = re.compile(r"### 插件配置项\s+```(?:\w+)?\s?([\s\S]*?)```")

RUNNER = """import json
import os
from dataclasses import asdict

from nonebot import init, load_plugin, require


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

init()
plugin = load_plugin("{}")

if not plugin:
    exit(1)
else:
    if plugin.metadata:
        metadata = asdict(
            plugin.metadata,
            dict_factory=lambda x: {{
                k: v for (k, v) in x if k not in ("config", "extra")
            }},
        )
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"METADATA<<EOF\\n{{json.dumps(metadata, cls=SetEncoder)}}\\nEOF\\n")

{}
"""


def get_plugin_list() -> dict[str, str]:
    """获取插件列表

    通过 package_name 获取 module_name
    """
    with urlopen(STORE_PLUGINS_URL) as response:
        plugins = json.loads(response.read())

    return {plugin["project_link"]: plugin["module_name"] for plugin in plugins}


class PluginTest:
    def __init__(
        self, project_link: str, module_name: str, config: str | None = None
    ) -> None:
        self._path = Path("plugin_test") / f"{project_link}-test"

        self.project_link = project_link
        self.module_name = module_name
        self.config = config

        self._create = False
        self._run = False
        self._deps = []

        self._output_lines: list[str] = []

        self._plugin_list = get_plugin_list()

    async def run(self):
        await self.create_poetry_project()
        if self._create:
            await self.show_package_info()
            await self.show_plugin_dependencies()
            await self.run_poetry_project()

        # 输出测试结果
        with open(GITHUB_OUTPUT_FILE, "a") as f:
            f.write(f"RESULT={self._run}\n")
        # 输出测试输出
        output = "\n".join(self._output_lines)
        # 限制输出长度，防止评论过长，评论最大长度为 65536
        output = output[:50000]
        with open(GITHUB_OUTPUT_FILE, "a") as f:
            f.write(f"OUTPUT<<EOF\n{output}\nEOF\n")
        # 输出至作业摘要
        with open(GITHUB_STEP_SUMMARY_FILE, "a") as f:
            summary = f"插件 {self.project_link} 加载测试结果：{'通过' if self._run else '未通过'}\n"
            summary += f"<details><summary>测试输出</summary><pre><code>{output}</code></pre></details>"
            f.write(f"{summary}")
        return self._run, output

    async def create_poetry_project(self) -> None:
        if not self._path.exists():
            proc = await create_subprocess_shell(
                f"poetry new {self._path.resolve()} && cd {self._path.resolve()} && poetry add {self.project_link} && poetry run python -m pip install -U pip {self.project_link}",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            code = proc.returncode

            self._create = not code
            if self._create:
                print(f"项目 {self.project_link} 创建成功。")
            else:
                self._log_output(f"项目 {self.project_link} 创建失败：")
                for i in stderr.decode().strip().splitlines():
                    self._log_output(f"    {i}")
        else:
            self._log_output(f"项目 {self.project_link} 已存在，跳过创建。")
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
                self._log_output(f"插件 {self.project_link} 的信息如下：")
                for i in stdout.decode().strip().splitlines():
                    self._log_output(f"    {i}")
            else:
                self._log_output(f"插件 {self.project_link} 信息获取失败。")

    async def show_plugin_dependencies(self) -> None:
        if self._path.exists():
            proc = await create_subprocess_shell(
                f"cd {self._path.resolve()} && poetry export --without-hashes",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            code = proc.returncode
            if not code:
                self._log_output(f"插件 {self.project_link} 依赖的插件如下：")
                for i in stdout.decode().strip().splitlines():
                    module_name = self._get_plugin_module_name(i)
                    if module_name:
                        self._deps.append(module_name)
                self._log_output(f"    {', '.join(self._deps)}")
            else:
                self._log_output(f"插件 {self.project_link} 依赖获取失败。")

    async def run_poetry_project(self) -> None:
        if self._path.exists():
            # 默认使用 ~none 驱动
            with open(self._path / ".env", "w") as f:
                f.write("DRIVER=~none\nLOGURU_COLORIZE=false")
            # 如果提供了插件配置项，则写入配置文件
            if self.config is not None:
                with open(self._path / ".env.prod", "w") as f:
                    f.write(self.config)

            with open(self._path / "runner.py", "w") as f:
                f.write(
                    RUNNER.format(
                        self.module_name,
                        "\n".join([f"require('{i}')" for i in self._deps]),
                    )
                )

            proc = await create_subprocess_shell(
                f"cd {self._path.resolve()} && poetry run python runner.py",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            code = proc.returncode

            self._run = not code

            status = "正常" if self._run else "出错"
            self._log_output(f"插件 {self.module_name} 加载{status}：")

            _out = stdout.decode().strip().splitlines()
            _err = stderr.decode().strip().splitlines()
            for i in _out:
                self._log_output(f"    {i}")
            for i in _err:
                self._log_output(f"    {i}")

    def _log_output(self, output: str) -> None:
        """记录输出，同时打印到控制台"""
        print(output)
        self._output_lines.append(output)

    def _get_plugin_module_name(self, require: str) -> str | None:
        # anyio==3.6.2 ; python_version >= "3.11" and python_version < "4.0"
        # pydantic[dotenv]==1.10.6 ; python_version >= "3.10" and python_version < "4.0"
        match = re.match(r"^(.+?)(?:\[.+\])?==", require.strip())
        if match:
            package_name = match.group(1)
            # 不用包括自己
            if package_name in self._plugin_list and package_name != self.project_link:
                return self._plugin_list[package_name]


async def test_plugin():
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        print("未找到 GITHUB_EVENT_PATH，已跳过")
        return

    with open(event_path, encoding="utf8") as f:
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
    config = CONFIG_PATTERN.search(issue_body)

    if not project_link or not module_name:
        print("议题中没有插件信息，已跳过")
        return

    # 测试插件
    test = PluginTest(
        project_link.group(1).strip(),
        module_name.group(1).strip(),
        config.group(1).strip() if config else None,
    )
    await test.run()


METADATA_PATTERN = re.compile(r"METADATA<<EOF\s([\s\S]+?)\sEOF")


def check_metadata(path: Path) -> bool:
    """检查插件是否拥有插件元数据"""
    with open(path / "output.txt") as f:
        output = f.read()
    match = METADATA_PATTERN.search(output)
    return bool(match)


async def test_store(offset: int, limit: int):
    global GITHUB_OUTPUT_FILE, GITHUB_STEP_SUMMARY_FILE

    plugin_test_path = Path("plugin_test")
    output_path = plugin_test_path / "output"
    output_path.mkdir(exist_ok=True)

    test_results = {}
    for i, (project_link, module_name) in enumerate(
        list(get_plugin_list().items())[offset:]
    ):
        if project_link.startswith("git+http"):
            continue
        if i >= limit:
            break
        print(f"正在测试插件 {project_link} ...")
        test = PluginTest(project_link, module_name)
        # 设置环境变量
        GITHUB_OUTPUT_FILE = (test._path / "output.txt").resolve()
        GITHUB_STEP_SUMMARY_FILE = (test._path / "summary.txt").resolve()
        os.environ["GITHUB_OUTPUT"] = str(GITHUB_OUTPUT_FILE)
        # 获取测试结果
        result, output = await test.run()
        test_results[project_link] = {
            "run": result,
            "metadata": check_metadata(test._path),
        }
        with open(output_path / f"{project_link}.log", "w", encoding="utf8") as f:
            f.write(output)
        with open(plugin_test_path / "results.json", "w", encoding="utf8") as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--store", action="store_true", help="测试插件商店内的插件")
    parser.add_argument("-l", "--limit", type=int, default=1, help="测试插件数量")
    parser.add_argument("-o", "--offset", type=int, default=0, help="测试插件偏移量")
    args = parser.parse_args()
    if args.store:
        print("测试插件商店内的插件")
        await test_store(args.offset, args.limit)
    else:
        await test_plugin()


if __name__ == "__main__":
    run(main())
