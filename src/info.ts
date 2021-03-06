import {AdapterInfo} from './types/adapter'
import {BotInfo} from './types/bot'
import {PluginInfo} from './types/plugin'

/** 更新文件所需信息 */
export type Info = BotInfo | PluginInfo | AdapterInfo

/** 发布类型 */
export type PublishType = 'Plugin' | 'Adapter' | 'Bot'
