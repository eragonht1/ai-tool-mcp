# AI-Tool MCP

基于FastMCP的AI工具集合，提供文件操作、系统监控、下载和PowerShell功能。

**🎯 总计20个工具，功能完整，架构清晰**

## 功能特性

### 📁 文件操作服务 (file_*) - 12个工具
- **基础操作**: 文件读写、追加、编辑
- **目录管理**: 创建、删除、列表
- **文件管理**: 复制、移动、删除、权限修改
- **批量支持**: 所有操作均支持批量处理
- **安全保障**: 强制绝对路径，防止路径遍历

### 📥 下载服务 (download_*) - 2个工具
- **智能下载**: 多文件并发下载，支持重试和超时
- **文件信息**: 远程文件信息获取（大小、类型等）
- **安全验证**: 文件类型安全检查
- **按需创建**: 目录按需创建，不预先占用空间

### 🖥️ 系统监控服务 (system_*) - 1个工具
- **基础信息**: 操作系统、硬件、网络信息
- **开发环境**: Python、Node.js版本和路径检测
- **隐私保护**: 仅提供必要的系统信息

### ⚡ PowerShell服务 (ps_*) - 5个工具
- **命令执行**: 快速执行PowerShell命令，支持3秒超时机制
- **会话管理**: UUID格式会话ID，支持多会话并发操作
- **GUI界面**: 单窗口多标签页设计，实时显示命令执行过程
- **用户控制**: AI查看输出需要用户确认，保护隐私安全
- **双向操作**: AI和用户可同时操作同一PowerShell会话

## 安装配置

### 环境要求
- **Python**: 3.8+ (推荐3.12+)
- **PowerShell**: 7.0+ (推荐7.5+)，路径：`C:\Program Files\PowerShell\7\pwsh.exe`
- **操作系统**: Windows 10+ (PowerShell功能需要)

### 安装依赖
```bash
# 推荐：使用requirements.txt安装所有依赖
cd ai-tool-mcp
pip install -r requirements.txt

# 或者手动安装核心依赖
pip install fastmcp requests psutil validators aiofiles customtkinter Pillow pydantic

# 开发环境额外安装
pip install ruff pytest pytest-asyncio
```

### MCP配置
在MCP客户端配置文件中添加：
```json
{
  "mcpServers": {
    "ai-tool-mcp": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/ai-tool-mcp"
    }
  }
}
```

### 启动服务
```bash
# 直接启动
python server.py

# 或使用模块方式
python -m ai-tool-mcp
```

## 使用示例

### 📁 文件操作
```python
# 读取文件（支持多种编码）
file_read(file_path="C:\\path\\to\\file.txt", encoding="utf-8")

# 写入文件
file_write(file_path="C:\\path\\to\\new.txt", content="Hello World", encoding="utf-8")

# 批量复制文件
file_copy(operations=[
    {"source": "C:\\src\\file1.txt", "dest": "C:\\dst\\file1.txt"},
    {"source": "C:\\src\\file2.txt", "dest": "C:\\dst\\file2.txt"}
])

# 创建目录
file_mkdir(dir_paths=["C:\\new\\folder1", "C:\\new\\folder2"])

# 获取文件信息
file_info(file_path="C:\\path\\to\\file.txt")
```

### 📥 下载文件
```python
# 单文件下载
download_get(
    urls="https://example.com/file.zip",
    filenames="file.zip",
    output_dir="C:\\Downloads"
)

# 批量下载
download_get(
    urls=["https://example.com/file1.zip", "https://example.com/file2.zip"],
    filenames=["file1.zip", "file2.zip"],
    output_dir="C:\\Downloads",
    max_concurrent=5
)

# 获取文件信息
download_info(url="https://example.com/file.zip")
```

### 🖥️ 系统监控
```python
# 获取系统基本信息
system_info()

# 返回信息包含：
# - 操作系统版本、计算机名
# - CPU型号、内存使用情况
# - 网络配置信息
# - Python、Node.js开发环境
```

### ⚡ PowerShell操作

#### 基本使用
```python
# 快速执行PowerShell命令（创建新会话）
ps_run(
    command="Get-Process | Select-Object -First 5",
    working_dir="C:\\Users"  # 必须使用绝对路径
)
# 返回：会话ID + 命令输出（3秒内完成）或超时提示

# 向现有会话追加命令（高效连续操作）
ps_append(
    session_id="f7952ab6-9be8-4d8c-b679-6830be3206b8",
    command="Get-Location"
)

# 获取终端输出（需用户确认）
ps_get(session_id="f7952ab6-9be8-4d8c-b679-6830be3206b8")

# 关闭PowerShell会话
ps_close(session_id="f7952ab6-9be8-4d8c-b679-6830be3206b8")

# 列出所有活跃会话
ps_list()
```

#### 高效使用策略
```python
# ✅ 推荐：批量操作使用同一会话
session = ps_run(command="Get-Location", working_dir="C:\\Project")
ps_append(session_id=session["session_id"], command="npm install")
ps_append(session_id=session["session_id"], command="npm run build")
ps_close(session_id=session["session_id"])

# ❌ 避免：频繁创建新会话
ps_run(command="Get-Location", working_dir="C:\\Project")
ps_run(command="npm install", working_dir="C:\\Project")  # 低效
ps_run(command="npm run build", working_dir="C:\\Project")  # 低效
```

#### GUI界面特性
- **自动弹出**：首次调用`ps_run`时自动显示GUI界面
- **多标签页**：每个会话对应一个标签页，支持同时查看多个终端
- **实时同步**：AI执行的命令在GUI中实时显示
- **用户操作**：用户可直接在GUI中输入命令，与AI共享同一会话
- **隐私保护**：AI查看输出时需要用户确认，点击确认按钮才返回结果

#### 注意事项
- **绝对路径**：`working_dir`参数必须使用绝对路径（如`C:\\Users\\Username`）
- **会话管理**：及时关闭不需要的会话，避免资源占用
- **超时机制**：命令执行超过3秒会返回会话ID，可用`ps_get`查看完整结果
- **编码支持**：自动处理中文编码，支持UTF-8、GBK等多种编码格式
- **ANSI序列**：输出中的`\u001b[32;1m`等是正常的颜色格式化代码

## 🔒 安全特性

### 通用安全
- **绝对路径强制**: 所有路径参数必须使用绝对路径，防止相对路径攻击
- **文件类型验证**: 下载文件的类型安全检查，支持白名单机制
- **路径验证**: 防止路径遍历攻击，确保操作在允许范围内

### PowerShell安全
- **用户确认机制**: AI查看PowerShell输出需要用户明确确认，保护隐私安全
- **会话隔离**: 每个PowerShell会话独立运行，避免相互影响
- **执行策略**: 使用`-ExecutionPolicy Bypass`，但仅限于当前会话
- **工作目录限制**: 强制验证工作目录为绝对路径，防止意外操作
- **超时保护**: 3秒超时机制，防止长时间阻塞操作
- **进程管理**: 会话关闭时自动清理PowerShell进程，避免资源泄露

## 📁 项目结构

```
ai-tool-mcp/
├── core/                   # 核心模块
│   ├── __init__.py        # 核心初始化
│   ├── config.py          # 配置管理
│   ├── file_downloader.py # 文件下载器
│   ├── file_option.py     # 文件操作
│   ├── path_validator.py  # 路径验证
│   ├── powershell_core.py # PowerShell核心操作
│   └── system_monitor.py  # 系统监控
├── services/              # 服务模块
│   ├── base_service.py    # 基础服务类
│   ├── file_service.py    # 文件操作服务
│   ├── download_service.py # 下载服务
│   ├── powershell_service.py # PowerShell服务
│   ├── powershell_gui.py  # PowerShell GUI界面
│   └── system_service.py  # 系统监控服务
├── tests/                 # 测试文件
├── logs/                  # 日志文件（自动创建）
├── server.py             # 主服务器入口
├── mcp.json              # MCP配置
├── requirements.txt      # 项目依赖文件
├── .env.example          # 环境变量示例
└── 核心.md               # 项目核心文档
```

## 🛠️ 开发说明

### 添加新工具
1. 在对应服务文件中使用 `@self.tool()` 装饰器
2. 参数使用 `Annotated[type, Field(description="...")]` 类型注解
3. 路径参数必须验证绝对路径格式
4. 异步函数使用 `async def`，同步函数直接定义

### PowerShell开发注意事项
1. **编码处理**: 使用多重编码尝试（UTF-8 → GBK → CP936 → Latin-1）
2. **GUI线程**: CustomTkinter必须在主线程运行，避免线程冲突
3. **会话管理**: 使用线程锁保护会话操作，确保线程安全
4. **进程清理**: 会话关闭时必须正确清理PowerShell进程
5. **用户确认**: 实现模态对话框，确保用户明确选择是否返回结果

### 配置管理
- 环境变量配置：复制 `.env.example` 为 `.env` 并修改
- 日志配置：自动轮转，默认10MB，保留5个备份
- 路径配置：支持Windows绝对路径验证

### 代码质量
```bash
# 代码格式化和检查
python code_quality_check.py

# 使用Ruff进行代码检查
ruff check .
ruff format .
```

## 📊 工具统计

| 服务 | 工具数量 | 主要功能 |
|------|----------|----------|
| 文件操作 | 12个 | 完整的文件和目录管理 |
| 下载服务 | 2个 | 文件下载和信息获取 |
| 系统监控 | 1个 | 系统信息获取 |
| PowerShell | 5个 | PowerShell命令执行和会话管理 |
| **总计** | **20个** | **功能完整的AI工具集** |

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
