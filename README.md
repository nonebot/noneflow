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

自动处理商店发布议题和测试插件

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
  cancel-in-progress: false

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
              "adapter_path": "website/static/adapters.json",
              "registry_repository": "nonebot/registry"
            }
        env:
          PLUGIN_TEST_RESULT: ${{ needs.plugin_test.outputs.result }}
          PLUGIN_TEST_OUTPUT: ${{ needs.plugin_test.outputs.output }}
          PLUGIN_TEST_METADATA: ${{ needs.plugin_test.outputs.metadata }}
          APP_ID: ${{ secrets.APP_ID }}
          PRIVATE_KEY: ${{ secrets.APP_KEY }}
          PRE_COMMIT_HOME: /github/workspace/.cache/.pre-commit

      - name: Fix permission
        run: sudo chown -R $(whoami):$(id -ng) .cache/.pre-commit
```

定时测试商店内插件

```yaml
name: "NoneBot Store Test"

on:
  workflow_dispatch:
    inputs:
      offset:
        description: "Offset"
        required: false
        default: "0"
      limit:
        description: "Limit"
        required: false
        default: "1"
      args:
        description: "Args"
        required: false
        default: ""
  schedule:
    - cron: "0 */4 * * *"
  repository_dispatch:
    types: [registry_update]

concurrency:
  group: "store-test"
  cancel-in-progress: false

jobs:
  store_test:
    runs-on: ubuntu-latest
    name: NoneBot2 plugin test
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        with:
          repository: nonebot/noneflow
          fetch-depth: 0
      - name: Install poetry
        run: pipx install poetry
      - uses: actions/setup-python@v4
        with:
          python-version: "3.10"
      - name: Prepare test
        run: |
          git checkout `git describe --abbrev=0 --tags`
          poetry install
          mkdir -p plugin_test/store
          curl -sSL https://raw.githubusercontent.com/nonebot/registry/results/results.json -o plugin_test/store/results.json
          curl -sSL https://raw.githubusercontent.com/nonebot/nonebot2/master/website/static/plugins.json -o plugin_test/store/plugins.json
          curl -sSL https://raw.githubusercontent.com/nonebot/nonebot2/master/website/static/bots.json -o plugin_test/bots.json
          curl -sSL https://raw.githubusercontent.com/nonebot/nonebot2/master/website/static/adapters.json -o plugin_test/adapters.json
      - name: Test plugin
        if: ${{ !contains(fromJSON('["Bot", "Adapter", "Plugin"]'), github.event.client_payload.type) }}
        run: |
          poetry run python -m src.utils.store_test --offset ${{ github.event.inputs.offset || 0 }} --limit ${{ github.event.inputs.limit || 50 }} ${{ github.event.inputs.args }}
      - name: Update registry(Plugin)
        if: github.event.client_payload.type == 'Plugin'
        run: poetry run python -m src.utils.store_test -k '${{ github.event.client_payload.key }}' -f
        env:
          PLUGIN_CONFIG: ${{ github.event.client_payload.config }}
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: results
          path: |
            ${{ github.workspace }}/plugin_test/results.json
            ${{ github.workspace }}/plugin_test/plugins.json
            ${{ github.workspace }}/plugin_test/bots.json
            ${{ github.workspace }}/plugin_test/adapters.json
  upload_results:
    runs-on: ubuntu-latest
    name: Upload results
    needs: store_test
    permissions:
      contents: write
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        with:
          ref: results
      - name: Download results
        uses: actions/download-artifact@v3
        with:
          name: results
          path: ${{ github.workspace }}
      - name: Push results
        run: |
          git config user.name github-actions[bot]
          git config user.email github-actions[bot]@users.noreply.github.com
          git add .
          git diff-index --quiet HEAD || git commit -m "chore: update test results"
          git push
  upload_results_netlify:
    runs-on: ubuntu-latest
    name: Upload results to netlify
    needs: store_test
    permissions:
      contents: read
      deployments: write
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        with:
          ref: main
      - name: Download results
        uses: actions/download-artifact@v3
        with:
          name: results
          path: ${{ github.workspace }}/websites
      - name: Get Branch Name
        run: echo "BRANCH_NAME=$(echo ${GITHUB_REF#refs/heads/})" >> $GITHUB_ENV
      - name: Deploy to Netlify
        uses: nwtgck/actions-netlify@v2
        with:
          publish-dir: "./websites"
          production-deploy: true
          github-token: ${{ secrets.GITHUB_TOKEN }}
          deploy-message: "Deploy ${{ env.BRANCH_NAME }}@${{ github.sha }}"
          enable-commit-comment: false
          alias: ${{ env.BRANCH_NAME }}
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
```

## 测试

在 [action-test](https://github.com/he0119/action-test) 仓库中测试。
