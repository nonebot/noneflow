/**机器人所需要的信息 */
export interface BotInfo {
  type: 'Bot'
  /**机器人名称 */
  name: string
  /**机器人介绍 */
  desc: string
  /**仓库/主页链接 */
  repo: string
  /**开发者 */
  author: string
}

/**从议题内容提取机器人信息 */
export function extractInfo(body: string, author: string): BotInfo {
  const nameRegexp = /- name: (.+)/
  const descRegexp = /- desc: (.+)/
  const repoRegexp = /- repo: (.+)/

  const nameMatch = body.match(nameRegexp)
  const name = nameMatch ? nameMatch[1] : null
  const descMatch = body.match(descRegexp)
  const desc = descMatch ? descMatch[1] : null
  const repoMatch = body.match(repoRegexp)
  const repo = repoMatch ? repoMatch[1] : null

  if (desc && name && repo) {
    return {
      type: 'Bot',
      author,
      desc,
      name,
      repo
    }
  }
  throw new Error('无法匹配成功')
}
