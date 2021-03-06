/**协议所需要的信息 */
export interface AdapterInfo {
  type: 'Adapter'
  /**import id */
  id: string
  /**pip地址 */
  link: string
  /**你的协议名称 */
  name: string
  /**简短描述协议 */
  desc: string
  /**开发者 */
  author: string
  /**插件项目仓库/主页链接 */
  repo: string
}

/**机器人所需要的信息 */
export interface BotInfo {
  type: 'Bot'
  /**机器人名称 */
  name: string
  /**简短描述机器人 */
  desc: string
  /**机器人项目仓库/主页链接 */
  repo: string
  /**开发者 */
  author: string
}

/**插件所需要的信息 */
export interface PluginInfo {
  type: 'Plugin'
  /**import id */
  id: string
  /**pip地址 */
  link: string
  /**你的插件名称 */
  name: string
  /**简短描述插件功能 */
  desc: string
  /**开发者 */
  author: string
  /**插件项目仓库/主页链接 */
  repo: string
}

export type Info = BotInfo | PluginInfo | AdapterInfo

export type IssueType = 'Plugin' | 'Adapter' | 'Bot'
