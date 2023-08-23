# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/zh-CN/spec/v2.0.0.html).

## [Unreleased]

### Changed

- 商店插件列表增加插件测试时的版本号
- 调整商店测试验证输出

## [2.7.3] - 2023-08-07

### Added

- 使用新版 none 驱动器提供的 exit 函数

### Changed

- 统一称呼将 PyPI 项目与包区分开来
- 检查网址的时候允许重定向

## [2.7.2] - 2023-07-08

### Fixed

- 补上忘记的 drivers.json 文件
- 修复 pre-commit cache 文件夹不存在时的报错

## [2.7.1] - 2023-07-02

### Fixed

- 修复 plugins 列表格式错误

## [2.7.0] - 2023-07-02

### Changed

- 调整商店测试输出格式

### Fixed

- 修复输出支持适配器列表未排序的问题

## [2.6.1] - 2023-06-26

### Added

- 将插件配置项传递给 registry

### Changed

- 商店测试结果中测试时间使用 isoformat

## [2.6.0] - 2023-06-26

### Added

- 拉取请求合并后触发 registry 更新
- 商店测试支持测试指定插件
- 生成新的商店插件列表

### Changed

- 使用新的商店测试结果结构

## [2.5.0] - 2023-06-23

### Fixed

- 插件测试输出去除 ANSI 字符

### Added

- 添加商店测试脚本

## [2.4.3] - 2023-06-14

### Changed

- 调整 pre-commit hooks 的存放位置至 .cache 目录下

## [2.4.2] - 2023-06-14

### Added

- 提交前先运行 pre-commit 统一格式

## [2.4.1] - 2023-06-12

### Added

- 限制名称的长度不超过 50 个字符

### Changed

- 通过议题标签判断商店发布类型

## [2.4.0] - 2023-06-11

### Added

- 直接从插件元数据中读取所需信息
- 支持测试时设置插件配置项

### Changed

- 无论发布是否通过检查都将修改议题标题

## [2.3.1] - 2023-05-13

### Fixed

- 修复插件测试数据匹配问题

## [2.3.0] - 2023-05-13

### Added

- 适配最新的议题模板

### Changed

- 自动合并时同时输出拉取请求的 ID

## [2.2.0] - 2023-04-10

### Added

- 跳过机器人的评论

### Changed

- 提前判断议题是否与发布有关

## [2.1.0] - 2023-04-08

### Added

- 遵守 debug logging 的设置

### Changed

- 优化评论内容
- 设置时区为中国
- 审查通过后如果可合并则直接合并

## [2.0.0] - 2023-04-07

### Added

- 审查通过后自动合并

### Changed

- 切换至 NoneBot
- 优化插件测试日志

## [1.2.1] - 2023-03-20

### Added

- 插件测试添加作业摘要
- 评论加上指向作业摘要的链接

## [1.2.0] - 2023-03-16

### Added

- 测试插件是否在 import 前使用 require 声明依赖

## [1.1.2] - 2023-02-10

### Added

- 运行命令出错时添加输出
- 升级 Python 至 3.11 版本

### Fixed

- 修复 git 命令报错的问题

## [1.1.1] - 2023-02-09

### Added

- 输出当前插件的信息
- 添加修改提示

### Fixed

- rc3 默认不自带 fastapi，修改为 none 驱动
- 修复插件测试中创建项目失败时，没有正确判断的问题
- 修复 Actions 排队后未能正确跳过关闭的议题的问题
- 修复拉取请求标签没有打上的问题

### Changed

- 优化运行条件，减少不必要的运行

## [1.1.0] - 2022-05-21

### Added

- 只有当文件发生变化后才强制推送
- 通过单独的测试脚本添加插件加载测试
- 评论内容无变化的时候，跳过修改

### Fixed

- 修复未同时修改议题与拉取请求标题的问题

### Changed

- 文件结尾加上换行符
- 抛弃 PyGithub 投入 githubkit 的怀抱

## [1.0.0] - 2022-05-21

### Added

- 添加检测是否重复发布

### Fixed

- 修复缺失信息时的错误匹配
- 修复当议题关闭仍然创建拉取请求的问题
- 修复解决冲突时没有重置的问题

### Changed

- 修改提交消息的格式，在最后添加上议题编号

### Removed

- 移除插件加载验证
- 移除 push 事件

## [0.5.2] - 2022-01-21

### Added

- 添加插件加载验证

### Fixed

- 拉取请求的标题少了冒号
- 处理合并冲突时，跳过未通过检查的发布

## [0.5.1] - 2022-01-06

### Added

- 添加针对 json 格式的检查

### Fixed

- 修复标签相关的报错

### Changed

- 使用自建的镜像以提升速度

## [0.5] - 2022-01-04

### Changed

- 利用 Python 重写 Action
- 更新至 beta1 的发布格式

## [0.4] - 2021-09-15

### Added

- 支持检查包是否发布到 PyPI
- 支持检查项目仓库/主页是否可以访问

## [0.3] - 2021-07-26

### Fixed

- 修改分支名为 publish

## [0.2] - 2020-11-20

### Changed

- 事件判定更严格
- 支持重开议题事件
- 检查拉取请求的标签是否为插件

### Fixed

- 拉取请求合并时报错
- 打开议题触发时，在插件信息中将仓库拥有者误设为插件作者

## [0.1] - 2020-11-19

### Added

- 最初的版本

[unreleased]: https://github.com/nonebot/noneflow/compare/v2.7.3...HEAD
[2.7.3]: https://github.com/nonebot/noneflow/compare/v2.7.2...v2.7.3
[2.7.2]: https://github.com/nonebot/noneflow/compare/v2.7.1...v2.7.2
[2.7.1]: https://github.com/nonebot/noneflow/compare/v2.7.0...v2.7.1
[2.7.0]: https://github.com/nonebot/noneflow/compare/v2.6.1...v2.7.0
[2.6.1]: https://github.com/nonebot/noneflow/compare/v2.6.0...v2.6.1
[2.6.0]: https://github.com/nonebot/noneflow/compare/v2.5.0...v2.6.0
[2.5.0]: https://github.com/nonebot/noneflow/compare/v2.4.3...v2.5.0
[2.4.3]: https://github.com/nonebot/noneflow/compare/v2.4.2...v2.4.3
[2.4.2]: https://github.com/nonebot/noneflow/compare/v2.4.1...v2.4.2
[2.4.1]: https://github.com/nonebot/noneflow/compare/v2.4.0...v2.4.1
[2.4.0]: https://github.com/nonebot/noneflow/compare/v2.3.1...v2.4.0
[2.3.1]: https://github.com/nonebot/noneflow/compare/v2.3.0...v2.3.1
[2.3.0]: https://github.com/nonebot/noneflow/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/nonebot/noneflow/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/nonebot/noneflow/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/nonebot/noneflow/compare/v1.2.1...v2.0.0
[1.2.1]: https://github.com/nonebot/noneflow/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/nonebot/noneflow/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/nonebot/noneflow/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/nonebot/noneflow/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/nonebot/noneflow/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/nonebot/noneflow/compare/v0.5.2...v1.0.0
[0.5.2]: https://github.com/nonebot/noneflow/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/nonebot/noneflow/compare/v0.5...v0.5.1
[0.5]: https://github.com/nonebot/noneflow/compare/v0.4...v0.5
[0.4]: https://github.com/nonebot/noneflow/compare/v0.3...v0.4
[0.3]: https://github.com/nonebot/noneflow/compare/v0.2...v0.3
[0.2]: https://github.com/nonebot/noneflow/compare/v0.1...v0.2
[0.1]: https://github.com/nonebot/noneflow/releases/tag/v0.1
