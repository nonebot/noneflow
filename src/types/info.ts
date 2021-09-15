import {AdapterInfo} from './adapter'
import {BotInfo} from './bot'
import {PluginInfo} from './plugin'

/** 更新文件所需信息 */
export type Info = BotInfo | PluginInfo | AdapterInfo

/** 发布类型 */
export type PublishType = 'Plugin' | 'Adapter' | 'Bot'
