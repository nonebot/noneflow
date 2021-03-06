import {PluginInfo} from '../info'

/**从议题内容提取插件信息 */
export function extractInfo(body: string, author: string): PluginInfo {
  const idRegexp = /- id: (.+)/
  const linkRegexp = /- link: (.+)/
  const descRegexp = /- desc: (.+)/
  const nameRegexp = /- name: (.+)/
  const repoRegexp = /- repo: (.+)/

  const idMatch = body.match(idRegexp)
  const id = idMatch ? idMatch[1] : null
  const linkMatch = body.match(linkRegexp)
  const link = linkMatch ? linkMatch[1] : null
  const descMatch = body.match(descRegexp)
  const desc = descMatch ? descMatch[1] : null
  const nameMatch = body.match(nameRegexp)
  const name = nameMatch ? nameMatch[1] : null
  const repoMatch = body.match(repoRegexp)
  const repo = repoMatch ? repoMatch[1] : null

  if (id && link && desc && name && repo) {
    return {
      type: 'Plugin',
      id,
      link,
      author,
      desc,
      name,
      repo
    }
  }
  throw new Error('无法匹配成功')
}
