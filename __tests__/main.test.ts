import {extractPluginInfo} from '../src/utils'

test('extract plugin info', async () => {
  const pluginPublish = `
**你的插件名称：**

复读机

**简短描述插件功能：**

复读群友的消息

**插件 import 使用的名称**

nonebot_plugin_example

**插件 install 使用的名称**

nonebot-plugin-example

**插件项目仓库/主页链接**

nonebot/nonebot2
`

  let pluginInfo = extractPluginInfo(pluginPublish, 'test')

  console.log(pluginInfo)
  expect(pluginInfo.id).toBe('nonebot_plugin_example')
  expect(pluginInfo.link).toBe('nonebot-plugin-example')
  expect(pluginInfo.author).toBe('test')
  expect(pluginInfo.desc).toBe('复读群友的消息')
  expect(pluginInfo.name).toBe('复读机')
  expect(pluginInfo.repo).toBe('nonebot/nonebot2')
})
