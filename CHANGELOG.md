# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/zh-CN/spec/v2.0.0.html).

## [Unreleased]

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

### Change

- 使用自建的镜像以提升速度

## [0.5.0] - 2022-01-04

### Changed

- 利用 Python 重写 Action
- 更新至 beta1 的发布格式

## [0.4.0] - 2021-09-15

### Added

- 支持检查包是否发布到 PyPI
- 支持检查项目仓库/主页是否可以访问

## [0.3.0] - 2021-07-26

### Fixed

- 修改分支名为 publish

## [0.2.0] - 2020-11-20

### Changed

- 事件判定更严格
- 支持重开议题事件
- 检查拉取请求的标签是否为插件

### Fixed

- 拉取请求合并时报错
- 打开议题触发时，在插件信息中将仓库拥有者误设为插件作者

## [0.1.0] - 2020-11-19

### Added

- 最初的版本

[unreleased]: https://github.com/nonebot/nonebot2-publish-bot/compare/v0.5.2...HEAD
[0.5.2]: https://github.com/nonebot/nonebot2-publish-bot/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/nonebot/nonebot2-publish-bot/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/nonebot/nonebot2-publish-bot/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/nonebot/nonebot2-publish-bot/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/nonebot/nonebot2-publish-bot/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/nonebot/nonebot2-publish-bot/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/nonebot/nonebot2-publish-bot/releases/tag/v0.1.0
