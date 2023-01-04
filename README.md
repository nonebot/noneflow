# NoneBot2 Publish Bot

[![codecov](https://codecov.io/gh/nonebot/nonebot2-publish-bot/branch/main/graph/badge.svg?token=BOIBTOCWCH)](https://codecov.io/gh/nonebot/nonebot2-publish-bot)

[NoneBot2](https://github.com/nonebot/nonebot2) 插件/协议/机器人 发布机器人

## 主要功能

根据 插件/协议/机器人 发布(带 Plugin/Adapter/Bot 标题)议题，自动修改对应文件，并创建拉取请求。

## 自动处理

- 商店发布议题创建后，自动根据议题内容创建拉取请求
- 相关议题修改时，自动修改已创建的拉取请求，如果没有创建则重新创建
- 拉取请求关闭时，自动关闭对应议题，并删除对应分支
- 已经创建的拉取请求在其他拉取请求合并后，自动解决冲突
- 自动检查是否符合发布要求

### 发布要求

- 项目主页能够访问
- 项目发布至 PyPI
- 插件能够正常加载

## 使用方法

简单的示例

```yaml
name: "NoneBot2 Publish Bot"

on:
  issues:
    types: [opened, reopened, edited]
  pull_request:
    types: [closed]
  issue_comment:
    types: [created]

concurrency:
  group: ${{ github.workflow }}-${{ github.event.issue.number || github.run_id }}
  cancel-in-progress: true

jobs:
  plugin_test:
    runs-on: ubuntu-latest
    name: nonebot2 plugin test
    permissions:
      issues: read
    outputs:
      result: ${{ steps.plugin-test.outputs.RESULT }}
      output: ${{ steps.plugin-test.outputs.OUTPUT }}
    steps:
      - name: Install poetry
        run: pipx install poetry
      - uses: actions/setup-python@v4
        with:
          python-version: "3.10"
      - name: Test Plugin
        id: plugin-test
        run: |
          curl -sSL https://raw.githubusercontent.com/nonebot/nonebot2-publish-bot/main/plugin_test.py -o plugin_test.py
          python plugin_test.py
  publish_bot:
    runs-on: ubuntu-latest
    name: nonebot2 publish bot
    needs: plugin_test
    steps:
      - name: Checkout code
        uses: actions/checkout@v2
      - name: NoneBot2 Publish Bot
        uses: docker://ghcr.io/nonebot/nonebot2-publish-bot:main
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          config: >
            {
              "base": "master",
              "plugin_path": "docs/.vuepress/public/plugins.json",
              "bot_path": "docs/.vuepress/public/bots.json",
              "adapter_path": "docs/.vuepress/public/adapters.json"
            }
        env:
          PLUGIN_TEST_RESULT: ${{ needs.plugin_test.outputs.result }}
          PLUGIN_TEST_OUTPUT: ${{ needs.plugin_test.outputs.output }}
```

## 测试

在 [action-test](https://github.com/he0119/action-test) 仓库中测试。
