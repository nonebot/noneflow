# NoneFlow

> NoneBot 商店工作流自动化机器人，基于 GitHub Actions + NoneBot2 构建

## 项目概览

- 运行环境：GitHub Actions 中的 NoneBot2 机器人，使用 `nonebot-adapter-github` 处理 webhook 事件
- 核心目标：自动处理 NoneBot 商店的插件/适配器/机器人 发布、修改、删除议题，生成 PR 并执行测试验证
- 主要组件：
  - `src/plugins/github/`：事件处理、GitHub/Git 操作
  - `src/providers/`：商店数据模型、校验逻辑、插件测试运行器

## 快速开始（本地）

- 安装依赖：`uv sync`
- 运行测试（并行 + 覆盖率）：`uv run poe test`
- 快照测试：
  - 创建快照：`uv run poe snapshot-create`
  - 更新快照：`uv run poe snapshot-fix`
- 本地运行 providers CLI：
  - 商店插件测试：`uv run poe store-test`
  - Docker 插件测试：`uv run poe docker-test`

## GitHub Actions 执行流程

1. `action.yml` 定义 Docker action
2. `docker/noneflow.dockerfile` 构建运行环境
3. `bot.py` 读取环境变量（`GITHUB_EVENT_NAME`、`GITHUB_EVENT_PATH`、`GITHUB_RUN_ID`）
4. 将 webhook payload 转换为 NoneBot Event 并分发到插件

## 代码结构与关键约定

### 插件加载机制

- `bot.py` 加载 `src/plugins/` 下所有插件
- `src/plugins/github/__init__.py` 动态加载子插件（`src/plugins/github/plugins/publish`、`remove`、`resolve` 等）
- 每个子插件通过 NoneBot matcher 监听特定 GitHub 事件（如 `issues.opened`、`pull_request.closed`）

### 配置模型（Pydantic）

- 主配置：`src/plugins/github/config.py`
  - `Config.model_config = coerce_numbers_to_str=True`：Actions 环境变量会被 NoneBot 强制转换
  - `input_config: PublishConfig`：嵌套配置，包含 `plugin_path`、`registry_repository`、`store_repository`、`artifact_path`

### GitHub/Git 操作规范

- Handler 类层次（`src/plugins/github/handlers/`）：
  - `GitHandler`：通过 `run_shell_command` 执行 git 命令（同步）
  - `GithubHandler`：封装 `githubkit` REST/GraphQL 调用（异步，方法前缀 `async_*`）
  - `IssueHandler`：继承 `GithubHandler`，维护 `issue.title`/`issue.body` 缓存，避免重复更新
- 关键约定：
  - 评论复用：通过 `NONEFLOW_MARKER = "<!-- NONEFLOW -->"` 标记已有评论并更新，避免重复发布
  - 跳过测试：在议题评论中使用 `/skip`（仅 OWNER/MEMBER 权限生效）
  - 分支命名：`BRANCH_NAME_PREFIX = "publish/issue"` + issue 编号

### 议题解析

- 使用正则表达式从议题 body 提取结构化信息（`src/plugins/github/utils.py` 的 `extract_issue_info_from_issue`）
- 模板：`### {字段名}\n\n{内容}`，见 `src/plugins/github/constants.py` 的 `ISSUE_PATTERN`

### 商店数据（store/registry）

- 数据模型：`src/providers/models.py`
  - `StorePlugin` / `StoreAdapter` 等：NoneBot 仓库存储格式
  - `RegistryPlugin` 等：商店 API 返回格式
- 校验逻辑：`src/providers/validation/`（主页可访问性、PyPI 版本、模块可加载性）
- JSON5 格式化约定：必须使用 `dump_json5`（`src/providers/utils.py`）写入文件，自动添加尾随逗号和换行

## 测试与质量

### 测试框架配置

- 使用 `nonebug` 测试 NoneBot 插件
- `pytest-asyncio`：所有异步测试自动标记为 `loop_scope="session"`（见 `tests/conftest.py`）
- `respx`：模拟所有外部 HTTP 调用（PyPI、GitHub API），禁止真实网络访问

### Fixture 说明

- `app` fixture（`tests/conftest.py`）：
  - 自动复制 `tests/store/` 下的 JSON5 文件到临时目录
  - Mock `plugin_config` 路径指向临时文件
  - 注意：`src/providers/` 不初始化 NoneBot，直接读取环境变量（如 `GITHUB_STEP_SUMMARY`）

### 时间 Mock

- 使用 `mock_datetime` fixture 固定时间为 `2023-08-23 09:22:14`（UTC+8），确保快照测试稳定

## 修改代码时的硬性规则

- 异步边界：GitHub API 调用必须 `async`/`await`；Git/文件操作必须走 `run_shell_command`（同步）
- 不要在同步上下文调用异步方法
- 议题解析修改需复用 `src/plugins/github/utils.py` 的正则辅助函数；常量集中在 `src/plugins/github/constants.py`
- 修改议题解析后必须更新相关测试快照
- JSON5 序列化必须使用 `dump_json5`，保持尾随逗号格式，避免无意义差异

## 提交与作者信息

- 提交信息通过 `commit_message` 辅助函数生成（`src/plugins/github/utils.py`）
- 格式：`{prefix} {message} (#{issue_number})`
- Git author 配置为议题提交者（`author@users.noreply.github.com`）

## 环境变量

### Actions 运行时必需

- `APP_ID` / `PRIVATE_KEY`：GitHub App 认证
- `GITHUB_EVENT_NAME` / `GITHUB_EVENT_PATH` / `GITHUB_RUN_ID`：Actions 上下文
- `GITHUB_STEP_SUMMARY`：输出作业摘要路径

### Providers CLI 使用

- `REGISTRY_UPDATE_PAYLOAD`：商店更新数据（JSON）
- `PROJECT_LINK` / `MODULE_NAME` / `PLUGIN_CONFIG`：Docker 测试参数
- `PYTHON_VERSION`：插件测试的 Python 版本
