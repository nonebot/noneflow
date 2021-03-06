import {extractInfo} from '../src/issue/adapter'

test('extract adapter info', async () => {
  const adapterPublish = `
  <!-- DO NOT EDIT ! -->
  <!--
  - id: nonebot.adapters.example
  - link: nonebot-adapter-example
  - name: example
  - desc: Example 协议
  - repo: nonebot/nonebot2
  -->
`

  let adapterInfo = extractInfo(adapterPublish, 'test')

  expect(adapterInfo.id).toBe('nonebot.adapters.example')
  expect(adapterInfo.link).toBe('nonebot-adapter-example')
  expect(adapterInfo.author).toBe('test')
  expect(adapterInfo.desc).toBe('Example 协议')
  expect(adapterInfo.name).toBe('example')
  expect(adapterInfo.repo).toBe('nonebot/nonebot2')
})
