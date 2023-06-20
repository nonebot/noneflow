""" 插件加载测试 

主要测试代码来自 https://github.com/Lancercmd/nonebot2-store-test
"""

import argparse
import json
import os
import re
import shutil
from asyncio import create_subprocess_shell, run, subprocess
from pathlib import Path
from typing import Any, TypedDict
from urllib.request import urlopen

# 插件测试目录
PLUGIN_TEST_PATH = Path("plugin_test")
if not PLUGIN_TEST_PATH.exists():
    PLUGIN_TEST_PATH.mkdir()
PLUGIN_TEST_OUTPUT_PATH = PLUGIN_TEST_PATH / "output"
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
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding='utf8') as f:
            f.write(f"METADATA<<EOF\\n{{json.dumps(metadata, cls=SetEncoder)}}\\nEOF\\n")

{}
"""


class PluginData(TypedDict):
    """NoneBot 商店插件数据"""

    module_name: str
    project_link: str
    name: str
    desc: str
    author: str
    homepage: str
    tags: list[Any]
    is_official: bool
    type: str
    supported_adapters: list[str]


class Metadata(TypedDict):
    """插件元数据"""

    name: str
    description: str
    homepage: str
    type: str
    supported_adapters: list[str]


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
        self.project_link = project_link
        self.module_name = module_name
        self.config = config

        self._create = False
        self._run = False
        self._deps = []

        self._output_lines: list[str] = []

        self._plugin_list = get_plugin_list()

    @property
    def key(self) -> str:
        """插件的标识符

        project_link-module_name
        例：nonebot-plugin-test-nonebot_plugin_test
        """
        return f"{self.project_link}-{self.module_name}"

    @property
    def path(self) -> Path:
        """插件测试目录"""
        return PLUGIN_TEST_PATH / f"{self.key}-test"

    async def run(self):
        await self.create_poetry_project()
        if self._create:
            await self.show_package_info()
            await self.show_plugin_dependencies()
            await self.run_poetry_project()

        # 输出测试结果
        with open(GITHUB_OUTPUT_FILE, "a", encoding="utf8") as f:
            f.write(f"RESULT={self._run}\n")
        # 输出测试输出
        output = "\n".join(self._output_lines)
        # 限制输出长度，防止评论过长，评论最大长度为 65536
        output = output[:50000]
        with open(GITHUB_OUTPUT_FILE, "a", encoding="utf8") as f:
            f.write(f"OUTPUT<<EOF\n{output}\nEOF\n")
        # 输出至作业摘要
        with open(GITHUB_STEP_SUMMARY_FILE, "a", encoding="utf8") as f:
            summary = f"插件 {self.project_link} 加载测试结果：{'通过' if self._run else '未通过'}\n"
            summary += f"<details><summary>测试输出</summary><pre><code>{output}</code></pre></details>"
            f.write(f"{summary}")
        return self._run, output

    def get_env(self) -> dict[str, str]:
        """获取环境变量

        删除虚拟环境变量，防止 poetry 使用运行当前脚本的虚拟环境
        """
        env = os.environ.copy()
        env.pop("VIRTUAL_ENV", None)
        return env

    async def create_poetry_project(self) -> None:
        if not self.path.exists():
            self.path.mkdir()
            proc = await create_subprocess_shell(
                f"""poetry init -n && sed -i "s/\\^/~/g" pyproject.toml && poetry config virtualenvs.in-project true --local && poetry env info && poetry add {self.project_link}""",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.path,
                env=self.get_env(),
            )
            stdout, stderr = await proc.communicate()
            code = proc.returncode

            self._create = not code
            if self._create:
                print(f"项目 {self.project_link} 创建成功。")
                for i in stdout.decode().strip().splitlines():
                    print(f"    {i}")
            else:
                self._log_output(f"项目 {self.project_link} 创建失败：")
                for i in stderr.decode().strip().splitlines():
                    self._log_output(f"    {i}")
        else:
            self._log_output(f"项目 {self.project_link} 已存在，跳过创建。")
            self._create = True

    async def show_package_info(self) -> None:
        if self.path.exists():
            proc = await create_subprocess_shell(
                f"poetry show {self.project_link}",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.path,
                env=self.get_env(),
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
        if self.path.exists():
            proc = await create_subprocess_shell(
                "poetry export --without-hashes",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.path,
                env=self.get_env(),
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
        if self.path.exists():
            # 默认使用 ~none 驱动
            with open(self.path / ".env", "w", encoding="utf8") as f:
                f.write("DRIVER=~none\nLOGURU_COLORIZE=false")
            # 如果提供了插件配置项，则写入配置文件
            if self.config is not None:
                with open(self.path / ".env.prod", "w", encoding="utf8") as f:
                    f.write(self.config)

            with open(self.path / "runner.py", "w", encoding="utf8") as f:
                f.write(
                    RUNNER.format(
                        self.module_name,
                        "\n".join([f"require('{i}')" for i in self._deps]),
                    )
                )

            proc = await create_subprocess_shell(
                "poetry run python runner.py",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.path,
                env=self.get_env(),
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


class StoreTest:
    """商店测试"""

    def __init__(self, offset: int = 0, limit: int = 1) -> None:
        self._offset = offset
        self._limit = limit

        # 输出文件位置
        self._plugin_test_path = PLUGIN_TEST_PATH
        self._result_path = self._plugin_test_path / "results.json"
        self._plugins_path = self._plugin_test_path / "plugins.json"
        if not self._plugins_path.exists():
            with open(self._plugins_path, "w", encoding="utf8") as f:
                f.write("[]")
        if not self._result_path.exists():
            self._result_path.touch()

        self._metadata_pattern = re.compile(r"METADATA<<EOF\s([\s\S]+?)\sEOF")

    def extract_metadata(self, path: Path) -> Metadata | None:
        """提取插件元数据"""
        with open(path / "output.txt", encoding="utf8") as f:
            output = f.read()
        match = self._metadata_pattern.search(output)
        if match:
            return json.loads(match.group(1))

    @staticmethod
    def strip_ansi(text: str | None) -> str:
        """去除 ANSI 转义字符"""
        if not text:
            return ""
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    async def validate_plugin(self, plugin: PluginData):
        """验证插件"""
        from datetime import datetime
        from zoneinfo import ZoneInfo

        project_link = plugin["project_link"]
        module_name = plugin["module_name"]

        test = PluginTest(project_link, module_name)

        # 设置环境变量
        global GITHUB_OUTPUT_FILE, GITHUB_STEP_SUMMARY_FILE
        GITHUB_OUTPUT_FILE = (test.path / "output.txt").resolve()
        GITHUB_STEP_SUMMARY_FILE = (test.path / "summary.txt").resolve()
        os.environ["GITHUB_OUTPUT"] = str(GITHUB_OUTPUT_FILE)

        # 获取测试结果
        result, output = await test.run()
        metadata = self.extract_metadata(test.path)
        metadata_result = await self.validate_metadata(result, plugin, metadata)

        # 测试完成后删除测试文件夹
        shutil.rmtree(test.path)

        return {
            "run": result,
            "output": self.strip_ansi(output),
            "valid": metadata_result["valid"],
            "metadata": metadata,
            "validation_message": self.strip_ansi(metadata_result["message"]),
            "validation_raw_data": metadata_result["raw"],
            "previous": plugin,
            "current": metadata_result["data"],
            "time": datetime.now(ZoneInfo("Asia/Shanghai")).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

    async def validate_metadata(
        self, result: bool, plugin: PluginData, metadata: Metadata | None
    ):
        """验证插件元数据"""
        import nonebot

        nonebot.init(
            input_config={
                "base": "",
                "plugin_path": str(self._plugins_path),
                "bot_path": "plugin_test/bots.json",
                "adapter_path": "plugin_test/adapters.json",
            },
            github_repository="nonebot/plugin-test",
            github_run_id=0,
            plugin_test_result="",
            plugin_test_output="",
        )
        from pydantic import ValidationError

        from src.plugins.publish.validation import PluginPublishInfo

        project_link = plugin["project_link"]
        module_name = plugin["module_name"]
        print(f"正在验证插件 {project_link}:{module_name} ...")

        if not metadata:
            return {
                "valid": False,
                "raw": None,
                "data": None,
                "message": "缺少元数据",
            }

        name = metadata.get("name")
        desc = metadata.get("description")
        homepage = metadata.get("homepage")
        type = metadata.get("type")
        supported_adapters = metadata.get("supported_adapters")

        raw_data = {
            "module_name": module_name,
            "project_link": project_link,
            "name": name,
            "desc": desc,
            "author": plugin["author"],
            "homepage": homepage,
            "tags": json.dumps(plugin["tags"]),
            "plugin_test_result": result,
            "type": type,
            "supported_adapters": supported_adapters,
        }
        try:
            publish_info = PluginPublishInfo(**raw_data)
            return {
                "valid": True,
                "raw": raw_data,
                "data": publish_info.dict(exclude={"plugin_test_result"}),
                "message": None,
            }
        except ValidationError as e:
            return {
                "valid": False,
                "raw": raw_data,
                "data": None,
                "message": str(e),
            }

    def get_previous_results(self):
        """获取上次测试结果"""
        import httpx

        resp = httpx.get(
            "https://raw.githubusercontent.com/he0119/nonebot-store-test/main/results/results.json"
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception("获取上次测试结果失败")

    def get_plugin_list(self) -> dict[str, PluginData]:
        """获取插件列表

        通过 package_name:module_name 获取插件信息
        """
        import httpx

        resp = httpx.get(STORE_PLUGINS_URL)
        if resp.status_code == 200:
            return {
                f'{plugin["project_link"]}:{plugin["module_name"]}': plugin
                for plugin in resp.json()
            }
        else:
            raise Exception("获取插件配置失败")

    def get_plugins_config(self):
        """获取插件配置"""
        import httpx

        resp = httpx.get(
            "https://raw.githubusercontent.com/he0119/nonebot-store-test/main/results/configs.json"
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception("获取插件配置失败")

    async def run(self):
        """测试商店内插件情况"""
        plugin_list = self.get_plugin_list()
        previous_results = self.get_previous_results()

        test_plugins = list(plugin_list.items())[
            self._offset : self._offset + self._limit
        ]

        current_results = {}
        total = len(test_plugins)
        for i, (key, plugin) in enumerate(test_plugins):
            if i >= self._limit:
                break
            if key.startswith("git+http"):
                continue

            print(f"{i+1}/{total} 正在测试插件 {key} ...")
            current_results[key] = await self.validate_plugin(plugin)

        results = {}
        # 按照插件列表顺序输出
        for key in plugin_list:
            # 如果当前测试结果中有，则使用当前测试结果
            # 否则使用上次测试结果
            if key in current_results:
                results[key] = current_results[key]
            elif key in previous_results:
                results[key] = previous_results[key]
        with open(self._result_path, "w", encoding="utf8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)


async def test_store(offset: int, limit: int):
    test = StoreTest(offset, limit)
    await test.run()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--store", action="store_true", help="测试插件商店内的插件")
    parser.add_argument("-l", "--limit", type=int, default=1, help="测试插件数量")
    parser.add_argument("-o", "--offset", type=int, default=0, help="测试插件偏移量")
    args = parser.parse_args()
    if args.store:
        await test_store(args.offset, args.limit)
    else:
        await test_plugin()


if __name__ == "__main__":
    run(main())
