import {extractInfo} from '../src/issue/bot'

test('extract bot info', async () => {
  const botPublish = `
  <!-- DO NOT EDIT ! -->
  <!--
  - name: coolqbot
  - desc: wow
  - repo: he0119/coolqbot
  -->
  -->
`

  let adapterInfo = extractInfo(botPublish, 'test')

  expect(adapterInfo.author).toBe('test')
  expect(adapterInfo.desc).toBe('wow')
  expect(adapterInfo.name).toBe('coolqbot')
  expect(adapterInfo.repo).toBe('he0119/coolqbot')
})
