import {extractAdapterInfo} from '../src/adapter'

test('extract adapter info', async () => {
  const adapterPublish = `
**你的协议名称：**

example

<!-- 协议连接时使用的名称：/<name>/ws -->

**简短描述协议：**

Example 协议

**插件 import 使用的名称**

nonebot.adapters.example

<!-- 或 nonebot_adapter_example 等合法包名 -->

**插件 install 使用的名称**

nonebot-adapter-example

<!--
例 1：nonebot-adapter-example

通过 pypi 安装

> 请事先发布插件到[pypi](https://pypi.org/)

例 2：git+https://github.com/nonebot/nonebot-adapter-example

从 github 仓库安装
-->

**插件项目仓库/主页链接**

nonebot/nonebot2

<!-- 默认 github 或其他完整链接，请勿使用 markdown 语法 -->
`

  let adapterInfo = extractAdapterInfo(adapterPublish, 'test')

  expect(adapterInfo.id).toBe('nonebot.adapters.example')
  expect(adapterInfo.link).toBe('nonebot-adapter-example')
  expect(adapterInfo.author).toBe('test')
  expect(adapterInfo.desc).toBe('Example 协议')
  expect(adapterInfo.name).toBe('example')
  expect(adapterInfo.repo).toBe('nonebot/nonebot2')
})
