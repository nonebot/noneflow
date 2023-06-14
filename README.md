<!-- markdownlint-disable -->
<p align="center">
  <a href="https://nonebot.dev/"><img src="https://raw.githubusercontent.com/nonebot/noneflow/main/assets/logo.png" width="200" alt="noneflow"></a>
</p>

<div align="center">

# NoneFlow

_✨ NoneBot 工作流管理机器人 ✨_

[![codecov](https://codecov.io/gh/nonebot/noneflow/branch/main/graph/badge.svg?token=BOIBTOCWCH)](https://codecov.io/gh/nonebot/noneflow)
[![Powered by NoneBot](https://img.shields.io/badge/Powered%20%20by-NoneBot-red)](https://github.com/nonebot/nonebot2)

</div>
<!-- markdownlint-enable-->

## 主要功能

根据 插件/协议/机器人 发布(带 Plugin/Adapter/Bot 标题)议题，自动修改对应文件，并创建拉取请求。

## 自动处理

- 商店发布议题创建后，自动根据议题内容创建拉取请求
- 相关议题修改时，自动修改已创建的拉取请求，如果没有创建则重新创建
- 拉取请求关闭时，自动关闭对应议题，并删除对应分支
- 已经创建的拉取请求在其他拉取请求合并后，自动解决冲突
- 自动检查是否符合发布要求
- 审查通过后自动合并

### 发布要求

- 项目主页能够访问
- 项目发布至 PyPI
- 插件能够正常加载

## 使用方法

简单的示例

```yaml
name: NoneFlow

on:
  issues:
    types: [opened, reopened, edited]
  pull_request_target:
    types: [closed]
  issue_comment:
    types: [created]
  pull_request_review:
    types: [submitted]

concurrency:
  group: ${{ github.workflow }}-${{ github.event.issue.number || github.run_id }}
  cancel-in-progress: true

jobs:
  plugin_test:
    runs-on: ubuntu-latest
    name: nonebot2 plugin test
    if: |
      !(
        (
          github.event.pull_request &&
          (
            github.event.pull_request.head.repo.fork ||
            !(
              contains(github.event.pull_request.labels.*.name, 'Plugin') ||
              contains(github.event.pull_request.labels.*.name, 'Adapter') ||
              contains(github.event.pull_request.labels.*.name, 'Bot')
            )
          )
        ) ||
        (
          github.event_name == 'issue_comment' && github.event.issue.pull_request
        )
      )
    permissions:
      issues: read
    outputs:
      result: ${{ steps.plugin-test.outputs.RESULT }}
      output: ${{ steps.plugin-test.outputs.OUTPUT }}
      metadata: ${{ steps.plugin-test.outputs.METADATA }}
    steps:
      - name: Install Poetry
        if: ${{ !startsWith(github.event_name, 'pull_request') }}
        run: pipx install poetry

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Test Plugin
        id: plugin-test
        run: |
          curl -sSL https://github.com/nonebot/noneflow/releases/latest/download/plugin_test.py | python -
  noneflow:
    runs-on: ubuntu-latest
    name: noneflow
    needs: plugin_test
    steps:
      - name: Generate token
        id: generate-token
        uses: tibdex/github-app-token@v1
        with:
          app_id: ${{ secrets.APP_ID }}
          private_key: ${{ secrets.APP_KEY }}

      - name: Checkout Code
        uses: actions/checkout@v3
        with:
          token: ${{ steps.generate-token.outputs.token }}

      - name: Cache pre-commit hooks
        uses: actions/cache@v3
        with:
          path: .cache/.pre-commit
          key: noneflow-${{ runner.os }}-${{ hashFiles('.pre-commit-config.yaml') }}

      - name: NoneFlow
        uses: docker://ghcr.io/nonebot/noneflow:latest
        with:
          config: >
            {
              "base": "master",
              "plugin_path": "website/static/plugins.json",
              "bot_path": "website/static/bots.json",
              "adapter_path": "website/static/adapters.json"
            }
        env:
          PLUGIN_TEST_RESULT: ${{ needs.plugin_test.outputs.result }}
          PLUGIN_TEST_OUTPUT: ${{ needs.plugin_test.outputs.output }}
          PLUGIN_TEST_METADATA: ${{ needs.plugin_test.outputs.metadata }}
          APP_ID: ${{ secrets.APP_ID }}
          PRIVATE_KEY: ${{ secrets.APP_KEY }}

      - name: Fix permission
        run: sudo chown -R $(whoami):$(id -ng) .cache/.pre-commit
```

## 测试

在 [action-test](https://github.com/he0119/action-test) 仓库中测试。
