# NoneFlow 项目指南

NoneFlow 是一个基于 NoneBot2 框架开发的 GitHub Actions 工作流管理机器人，用于自动化处理 NoneBot 生态中的插件、适配器和机器人发布流程。

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

## 测试

测试使用 pytest 框架，配置如下：

```bash
# 运行所有测试（并行）
uv run poe test

# 等同于
pytest --cov=src --cov-report xml --junitxml=./junit.xml -n auto
```

测试用例应按目录和多个文件组织，不要使用测试类。

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

## 版本管理

使用 `bump-my-version` 管理版本号：

```bash
# 显示当前版本和可升级版本
uv run poe show-bump

# 升级版本（自动修改 pyproject.toml、CHANGELOG.md、uv.lock）
uv run poe bump
```

## 开发注意事项

1. **GitHub App 权限**: 需要 `contents:write`、`issues:write`、`pull_requests:write` 等权限
2. **Docker 测试**: 插件测试需要 Docker 环境，测试时会拉取插件代码并在隔离环境中运行
3. **并发控制**: 使用 `concurrency` 配置避免同一议题的并发处理
4. **Artifact 传递**: 通过 GitHub Actions Artifact 在不同工作流间传递数据

## 相关仓库

- [nonebot2](https://github.com/nonebot/nonebot2): NoneBot 主仓库
- [adapter-github](https://github.com/nonebot/adapter-github): GitHub 协议适配
- [githubkit](https://github.com/yanyongyu/githubkit): GitHub API
- [registry](https://github.com/nonebot/registry): 商店注册表
- [noneflow-test](https://github.com/nonebot/noneflow-test): 测试仓库
