# NoneFlow 项目指南

NoneFlow 是一个基于 NoneBot2 框架开发的 GitHub Actions 工作流管理机器人，用于自动化处理 NoneBot 生态中的插件、适配器和机器人发布流程。

## 项目概述

NoneFlow 主要功能包括：

- 自动处理商店发布议题（Plugin/Adapter/Bot），根据议题内容创建拉取请求
- 自动修改已创建的拉取请求当议题内容变化时
- 拉取请求关闭时自动关闭对应议题并删除分支
- 自动解决已创建拉取请求的冲突
- 自动检查发布要求（主页可访问、已发布至 PyPI、插件可正常加载）
- 审查通过后自动合并

## 技术栈

- **Python**: 3.14.3+
- **框架**: NoneBot2 (异步机器人框架)
- **适配器**: nonebot-adapter-github
- **验证**: Pydantic v2
- **包管理**: uv
- **容器**: Docker
- **GitHub API**: githubkit

## 项目结构

```text
.
├── bot.py                  # 主入口，初始化 NoneBot 并处理 GitHub Actions 事件
├── pyproject.toml          # 项目配置、依赖和工具设置
├── action.yml              # GitHub Action 定义
├── src/
│   ├── plugins/
│   │   └── github/         # GitHub 事件处理插件
│   │       ├── plugins/
│   │       │   ├── publish/    # 发布处理（Plugin/Adapter/Bot）
│   │       │   ├── remove/     # 移除处理
│   │       │   ├── resolve/    # 冲突解决
│   │       │   └── config/     # 配置处理
│   │       ├── handlers/       # GitHub API 处理器
│   │       ├── depends/        # 依赖注入函数
│   │       └── config.py       # 插件配置
│   └── providers/
│       ├── validation/     # 数据验证模块
│       ├── docker_test/    # Docker 插件测试
│       ├── store_test/     # 商店测试
│       └── models.py       # 数据模型定义
├── tests/                  # 测试代码
├── docker/                 # Dockerfile 定义
│   ├── noneflow.dockerfile # NoneFlow 主镜像
│   └── nonetest.dockerfile # 插件测试镜像
└── examples/               # GitHub Actions 工作流示例
```

## 构建与运行

### 本地开发环境

项目使用 `uv` 作为包管理器：

```bash
# 安装依赖
uv sync

# 运行测试
uv run poe test

# 创建快照
uv run poe snapshot-create

# 修复快照
uv run poe snapshot-fix
```

### Docker 构建

```bash
# 构建 NoneFlow 镜像
docker build -f docker/noneflow.dockerfile -t noneflow .

# 构建 NoneTest 镜像（用于插件测试）
docker build -f docker/nonetest.dockerfile -t nonetest .
```

### GitHub Actions 运行

项目作为 GitHub Action 运行，配置示例见 `examples/noneflow.yml`：

```yaml
- name: NoneFlow
  uses: docker://ghcr.io/nonebot/noneflow:latest
  with:
    config: >
      {
        "base": "master",
        "plugin_path": "assets/plugins.json5",
        "bot_path": "assets/bots.json5",
        "adapter_path": "assets/adapters.json5",
        "registry_repository": "nonebot/registry"
      }
  env:
    APP_ID: ${{ secrets.APP_ID }}
    PRIVATE_KEY: ${{ secrets.APP_KEY }}
```

## 测试

测试使用 pytest 框架，配置如下：

```bash
# 运行所有测试（并行）
uv run poe test

# 等同于
pytest --cov=src --cov-report xml --junitxml=./junit.xml -n auto
```

### 测试结构

- `tests/conftest.py`: 全局测试配置和 fixtures
- `tests/plugins/github/`: GitHub 插件测试
- `tests/providers/`: Provider 模块测试
- `tests/constant.py`: 测试常量

### 关键测试 Fixtures

- `app`: NoneBot 应用实例
- `mocked_api`: 使用 respx 模拟的 HTTP API（PyPI、GitHub、商店数据）
- `mock_datetime`: 固定时间戳，确保测试一致性

## 代码风格

项目使用 Ruff 进行代码格式化和 lint：

- **行长度**: 88 字符
- **目标 Python 版本**: 3.13+
- **导入排序**: isort 规则启用
- **类型检查**: Pyright (standard 模式)

### 主要规则

- `F`, `W`, `E`: Pyflakes 和 pycodestyle
- `UP`: pyupgrade
- `ASYNC`: flake8-async
- `I`: isort 导入排序
- `RUF`: Ruff 特定规则

## 主要模块说明

### 1. GitHub 插件 (`src/plugins/github/`)

#### 发布处理 (`plugins/publish/`)

处理 Plugin/Adapter/Bot 的发布流程：

- `__init__.py`: 事件处理器（issue 打开/编辑/评论，PR 关闭/审查）
- `validation.py`: 议题内容验证逻辑
- `render.py`: 评论渲染
- `utils.py`: 工具函数

#### 移除处理 (`plugins/remove/`)

处理商店项目的移除请求。

#### 冲突解决 (`plugins/resolve/`)

自动解决多个发布 PR 之间的冲突。

#### 配置处理 (`plugins/config/`)

处理商店配置的修改。

### 2. 数据验证 (`src/providers/validation/`)

使用 Pydantic 模型验证发布数据：

- `PluginPublishInfo`: 插件发布信息
- `AdapterPublishInfo`: 适配器发布信息
- `BotPublishInfo`: 机器人发布信息
- `DriverPublishInfo`: 驱动器发布信息

### 3. Docker 测试 (`src/providers/docker_test/`)

在隔离的 Docker 环境中测试插件加载：

- 拉取插件代码
- 安装依赖
- 验证插件可正常加载
- 提取插件元数据

### 4. 数据模型 (`src/providers/models.py`)

核心数据模型：

- `StorePlugin`/`StoreAdapter`/`StoreBot`: 商店数据格式
- `RegistryPlugin`/`RegistryAdapter`/`RegistryBot`: 注册表数据格式
- `RegistryArtifactData`: GitHub Artifact 数据传递

## 配置说明

### 环境变量

- `APP_ID`: GitHub App ID
- `PRIVATE_KEY`: GitHub App 私钥
- `GITHUB_REPOSITORY`: 当前仓库
- `GITHUB_RUN_ID`: 工作流运行 ID
- `GITHUB_EVENT_NAME`: 事件名称
- `GITHUB_EVENT_PATH`: 事件文件路径
- `INPUT_CONFIG`: JSON 格式的配置

### 输入配置 (INPUT_CONFIG)

```json
{
  "base": "master", // 基础分支
  "plugin_path": "assets/plugins.json5", // 插件数据文件路径
  "bot_path": "assets/bots.json5", // 机器人数据文件路径
  "adapter_path": "assets/adapters.json5", // 适配器数据文件路径
  "registry_repository": "nonebot/registry", // 注册表仓库
  "store_repository": "nonebot/nonebot2", // 商店仓库
  "artifact_path": "artifact" // Artifact 存储路径
}
```

## 发布流程

1. 用户在仓库创建带 `Plugin`/`Adapter`/`Bot` 标签的议题
2. NoneFlow 自动检测议题并提取信息
3. 验证信息完整性（名称、主页、PyPI 项目等）
4. 如果是插件，在 Docker 中测试加载
5. 创建拉取请求修改商店数据文件
6. 审查通过后自动合并
7. 触发注册表更新

## 版本管理

使用 `bump-my-version` 管理版本号：

```bash
# 显示当前版本和可升级版本
uv run poe show-bump

# 升级版本（自动修改 pyproject.toml、CHANGELOG.md、uv.lock）
uv run poe bump
```

## CI/CD

### GitHub Actions 工作流

1. **CI** (`.github/workflows/main.yml`):
   - 运行测试
   - 上传覆盖率到 Codecov
   - 构建并推送 Docker 镜像

2. **Release Draft** (`.github/workflows/release-draft.yml`):
   - 自动生成发布草稿

### Docker 镜像

- `ghcr.io/nonebot/noneflow`: NoneFlow 主镜像
- `ghcr.io/nonebot/nonetest`: 插件测试镜像

## 开发注意事项

1. **GitHub App 权限**: 需要 `contents:write`、`issues:write`、`pull_requests:write` 等权限
2. **Docker 测试**: 插件测试需要 Docker 环境，测试时会拉取插件代码并在隔离环境中运行
3. **并发控制**: 使用 `concurrency` 配置避免同一议题的并发处理
4. **Artifact 传递**: 通过 GitHub Actions Artifact 在不同工作流间传递数据

## 相关仓库

- [nonebot2](https://github.com/nonebot/nonebot2): NoneBot 主仓库
- [registry](https://github.com/nonebot/registry): 商店注册表
- [noneflow-test](https://github.com/nonebot/noneflow-test): 测试仓库
