# NoneBot2 Plugin Issue Bot

[NoneBot2](https://github.com/nonebot/nonebot2) 插件/协议发布机器人

## 主要功能

根据插件发布(带 Plugin 标签)议题，自动修改 `plugins.json` 文件，并创建拉取请求。

## 自动处理

- 插件发布议题创建后，自动根据议题内容创建拉取请求
- 相关议题修改时，自动修改已创建的拉取请求，如果没有创建则重新创建
- 拉取请求关闭时，自动关闭对应议题，并删除对应分支
- 已经创建的拉取请求在其他拉取请求合并后，自动解决冲突

## 测试

在 [action-test](https://github.com/he0119/action-test) 仓库中测试。
