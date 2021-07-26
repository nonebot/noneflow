/**插件所需要的信息 */
export interface PluginInfo {
  type: 'Plugin'
  /**插件 import 包名 */
  id: string
  /**PyPI 项目名 */
  link: string
  /**插件名称 */
  name: string
  /**插件介绍 */
  desc: string
  /**仓库/主页链接 */
  repo: string
  /**开发者 */
  author: string
}

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
      name,
      desc,
      repo,
      author
    }
  }
  throw new Error('无法匹配成功')
}
