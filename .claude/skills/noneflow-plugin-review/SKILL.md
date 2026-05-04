# NoneFlow Plugin Code Review

name: noneflow-plugin-review
description: 审查 NoneBot2 插件源代码是否符合商店发布规范。输入插件仓库地址，参考 yanyongyu 的审查标准，检查插件元数据、配置读取、异步代码、依赖声明等，给出具体的修复建议。

## Scope

- 输入为插件 GitHub 仓库地址（如 `https://github.com/xxx/nonebot-plugin-xxx`）
- 仅审查公开可访问的仓库
- 专注于插件源代码质量审查，不处理 issue 或 PR

## Workflow

1. 获取插件仓库信息。

   - 从输入的仓库地址获取基本信息
   - 克隆或浏览源代码
   - 识别插件入口文件：`{module_name}/__init__.py`
   - 查找 `pyproject.toml` 或 `setup.py` 了解依赖

2. 审查插件元数据。
   检查 `__plugin_meta__` 是否正确定义：

   ```python
   from nonebot.plugin import PluginMetadata

   __plugin_meta__ = PluginMetadata(
       name="插件名称",
       description="插件描述",
       usage="/命令说明",
       type="application",  # 或 "library"
       homepage="https://github.com/...",
       supported_adapters={"~onebot.v11"},  # 或 None 表示全平台
       config=Config,  # 如有配置
   )
   ```

   常见问题：

   - 缺少 `__plugin_meta__` 定义
   - 使用 `__plugin_metadata__`（错误名称）
   - 缺少必要字段（name、description、usage）
   - `type` 不是 "application" 或 "library"
   - `supported_adapters` 格式错误

3. 审查配置处理。
   **必须使用 `get_plugin_config`**：

   ```python
   from nonebot import get_plugin_config
   from pydantic import BaseModel

   class Config(BaseModel):
       api_key: str = ""
       api_secret: str = ""

   config = get_plugin_config(Config)
   ```

   **错误示范**：

   ```python
   # ❌ 直接从环境变量读取
   from os import environ
   config = Config(**environ)

   # ❌ 使用 BaseSettings
   from pydantic import BaseSettings
   class Config(BaseSettings):
       ...
   ```

   **配置项命名**：

   - 必须小写：`api_key` ✅
   - 禁止大写：`API_KEY` ❌

4. 审查异步代码。
   **禁止同步网络请求**：

   ```python
   # ❌ 错误
   import requests
   response = requests.get(url)

   # ✅ 正确
   import httpx
   async with httpx.AsyncClient() as client:
       response = await client.get(url)

   # ✅ 正确
   import aiohttp
   async with aiohttp.ClientSession() as session:
       async with session.get(url) as response:
           data = await response.json()
   ```

   **常见问题**：

   - 使用 `requests` 库
   - 使用 `urllib`
   - 假异步（用 `asyncio.run` 包装同步代码）

5. 审查依赖声明。
   **插件依赖必须 require**：

   ```python
   # __init__.py 顶部
   from nonebot import require

   require("nonebot_plugin_alconna")
   require("nonebot_plugin_localstore")

   # 然后再 import
   from nonebot_plugin_alconna import Alconna
   ```

   **常见问题**：

   - 使用第三方插件但未 require
   - require 位置不在模块顶层
   - 在函数内部 require

   **Pydantic 兼容性**：

   ```python
   # ❌ 错误：限制 pydantic 版本
   # pyproject.toml
   dependencies = ["pydantic>=2.0"]

   # ✅ 正确：使用兼容方法
   from nonebot.compat import model_validator, field_validator
   ```

6. 审查数据存储。
   **必须使用 localstore 插件**：

   ```python
   from nonebot import require
   require("nonebot_plugin_localstore")

   from nonebot_plugin_localstore import get_plugin_data_dir, get_plugin_cache_dir

   # ✅ 缓存到变量，不要每次调用
   DATA_DIR = get_plugin_data_dir()
   CACHE_DIR = get_plugin_cache_dir()
   ```

   **错误示范**：

   ```python
   # ❌ 使用固定路径
   data_path = Path(__file__).parent / "data"

   # ❌ 每次调用都获取
   def save_data(data):
       path = get_plugin_data_dir() / "data.json"
   ```

7. 审查日志记录。
   **从 nonebot 导入 logger**：

   ```python
   from nonebot import logger

   logger.info("插件加载成功")
   logger.error("发生错误", exc_info=True)
   ```

   **错误示范**：

   ```python
   # ❌ 使用标准库 logging
   import logging
   logger = logging.getLogger(__name__)
   ```

8. 审查依赖管理。
   **删除无用依赖**：

   - 标准库不需要安装：`uuid`、`asyncio`、`json`、`os`
   - 未使用的依赖应该删除

   **版本约束**：

   ```toml
   # ❌ 错误：锁死版本
   dependencies = ["moviepy==1.0.3"]

   # ✅ 正确：范围限制
   dependencies = ["moviepy>=1.0.0,<2.0.0"]
   ```

9. 审查代码质量。
   **避免 monkey patch**：

   ```python
   # ❌ 错误：修改第三方包
   import some_lib
   some_lib.original_function = my_function

   # ✅ 正确：继承重写
   class MyLib(some_lib.BaseClass):
       def original_function(self):
           ...
   ```

   **无用 validator**：

   ```python
   # ❌ 错误：重复验证
   class Config(BaseModel):
       name: str

       @validator("name")
       def check_name(cls, v):
           if not isinstance(v, str):
               raise ValueError("must be string")
           return v

   # ✅ 正确：pydantic 已做类型检查
   class Config(BaseModel):
       name: str
   ```

10. 生成审查报告。
    汇总所有发现的问题，按优先级排序，给出具体修复建议。

## Code Review Checklist

### P0 - 必须修复（会阻止发布）

- [ ] **元数据定义**：`__plugin_meta__` 正确定义且字段完整
- [ ] **配置读取**：使用 `get_plugin_config` 而非直接读取环境变量
- [ ] **异步网络**：使用 `httpx`/`aiohttp` 而非 `requests`
- [ ] **依赖声明**：使用第三方插件前已 `require`
- [ ] **Pydantic 兼容**：未限制 pydantic v2，使用兼容写法

### P1 - 强烈建议修复（影响代码质量）

- [ ] **数据存储**：使用 `localstore` 插件获取目录
- [ ] **目录缓存**：`get_plugin_data_dir` 只调用一次并缓存
- [ ] **日志记录**：从 `nonebot` 导入 logger
- [ ] **配置命名**：配置项名称为小写
- [ ] **require 位置**：在模块顶层进行 require

### P2 - 建议优化（提升代码质量）

- [ ] **无 monkey patch**：未修改第三方包代码
- [ ] **无用依赖**：已删除未使用的依赖
- [ ] **版本约束**：未锁死依赖版本
- [ ] **无重复验证**：未添加 pydantic 已处理的 validator

## Common Issues

### 元数据缺失

- 现象：找不到 `__plugin_meta__` 定义
- 修复：在 `__init__.py` 中添加完整定义
- yanyongyu：`"插件元数据缺少支持的适配器"`

### 配置读取错误

- 现象：使用 `Config(**environ)` 或 `BaseSettings`
- 修复：改用 `get_plugin_config`
- yanyongyu：`"插件读取配置项的方式不正确，请参考配置文档使用 get_plugin_config"`

### 同步请求

- 现象：import requests
- 修复：改用 httpx 或 aiohttp
- yanyongyu：`"请不要使用requests进行同步网络请求"`

### 缺少 require

- 现象：直接 import 第三方插件
- 修复：在顶部添加 require
- yanyongyu：`"只要是用到的第三方插件都需要 require"`

### Pydantic 限制

- 现象：`pydantic>=2.0`
- 修复：删除版本限制，使用兼容方法
- yanyongyu：`"插件依赖限制了 pydantic 版本，请移除"`

### 数据存储错误

- 现象：使用固定路径或重复获取目录
- 修复：使用 localstore 并缓存
- yanyongyu：`"localstore 获取插件数据目录不要每次调用都获取一遍"`

### 配置项大写

- 现象：`API_KEY`、`SECRET`
- 修复：改为 `api_key`、`secret`
- yanyongyu：`"插件配置项的名称应为小写"`

### 日志方式错误

- 现象：`import logging`
- 修复：`from nonebot import logger`
- yanyongyu：`"插件 logger 应该从 nonebot 导入"`

## Output Format

## 插件审查报告

- 仓库：`https://github.com/xxx/nonebot-plugin-xxx`
- 模块名：`nonebot_plugin_xxx`
- 版本：`1.0.0`

## 审查结果

| 优先级 | 检查项        | 状态  | 问题描述 |
| ------ | ------------- | ----- | -------- |
| P0     | 元数据定义    | ✅/❌ | ...      |
| P0     | 配置读取      | ✅/❌ | ...      |
| P0     | 异步网络      | ✅/❌ | ...      |
| P0     | 依赖声明      | ✅/❌ | ...      |
| P0     | Pydantic 兼容 | ✅/❌ | ...      |
| P1     | 数据存储      | ✅/❌ | ...      |
| P1     | 日志记录      | ✅/❌ | ...      |
| P1     | 配置命名      | ✅/❌ | ...      |
| P2     | 无用依赖      | ✅/❌ | ...      |
| P2     | 版本约束      | ✅/❌ | ...      |

## 问题详情

### 问题 1：{问题标题}

**文件**：`plugin/__init__.py`
**行号**：L15
**严重程度**：P0

**当前代码**：

```python
import requests
response = requests.get(url)
```

**修复建议**：

```python
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

**yanyongyu 原话**：

> "请不要使用requests进行同步网络请求，请使用 httpx 或者 aiohttp 进行异步请求"

---

（更多问题...）

## 修复优先级

1. **立即修复**（P0）：

   - 问题 1
   - 问题 2

2. **建议修复**（P1）：

   - 问题 3
   - 问题 4

3. **可选优化**（P2）：
   - 问题 5

## 给开发者的建议

- 修复 P0 问题后才能通过商店审核
- 参考 NoneBot 插件开发文档：https://nonebot.dev/docs/developer/plugin-definition
- 参考配置文档：https://nonebot.dev/docs/advanced/config

## Reminders

- **优先检查 P0 问题**，这些问题会直接阻止发布
- **给出具体的代码修复示例**，不要只说"请修复"
- **引用 yanyongyu 的原话**作为权威参考
- **指向具体文件和行号**，方便开发者定位
- **如果代码已符合规范**，明确说明"审查通过"
