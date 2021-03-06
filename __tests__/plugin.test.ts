import {extractInfo} from '../src/issue/plugin'

test('extract plugin info', async () => {
  const pluginPublish = `
  <!-- DO NOT EDIT ! -->
  <!--
  - id: nonebot_plugin_example
  - link: nonebot-plugin-example
  - name: 复读机
  - desc: 复读群友的消息
  - repo: nonebot/nonebot2
  -->
`

  let pluginInfo = extractInfo(pluginPublish, 'test')

  expect(pluginInfo.id).toBe('nonebot_plugin_example')
  expect(pluginInfo.link).toBe('nonebot-plugin-example')
  expect(pluginInfo.author).toBe('test')
  expect(pluginInfo.desc).toBe('复读群友的消息')
  expect(pluginInfo.name).toBe('复读机')
  expect(pluginInfo.repo).toBe('nonebot/nonebot2')
})
