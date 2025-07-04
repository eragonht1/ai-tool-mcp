# AI-Tool MCP

基于FastMCP的AI工具集合，提供文件操作、PowerShell管理、系统监控和下载功能。

## 功能特性

### 文件操作服务 (file_*)
- 文件读写、复制、移动、删除
- 目录创建、删除、列表
- 文件权限管理
- 支持批量操作

### PowerShell管理服务 (ps_*)
- 执行PowerShell命令（强制绝对路径）
- 会话管理（创建、销毁、列表、统计）
- 安全验证和命令过滤
- 支持临时进程和持久会话

### 下载服务 (download_*)
- 多文件并发下载
- 文件信息获取
- 支持重试和超时控制
- 文件类型安全验证

### 系统监控服务 (system_*)
- CPU、内存、磁盘、网络监控
- 进程和服务状态
- GPU信息（如果可用）
- 实时系统信息
- 开发环境信息（Python、Node.js版本和路径）

## 安装配置

### 环境要求
- Python 3.8+
- Windows系统（PowerShell功能）

### 安装依赖
```bash
pip install fastmcp requests psutil
```

### MCP配置
在MCP客户端配置文件中添加：
```json
{
  "mcpServers": {
    "ai-tool-mcp": {
      "command": "python",
      "args": ["G:\\docker\\McpApi\\ai-tool-mcp\\__main__.py"],
      "cwd": "G:\\docker\\McpApi\\ai-tool-mcp"
    }
  }
}
```

## 使用示例

### 文件操作
```python
# 读取文件
file_read("C:\\path\\to\\file.txt")

# 批量复制文件
file_copy([
    {"source": "C:\\src\\file1.txt", "dest": "C:\\dst\\file1.txt"},
    {"source": "C:\\src\\file2.txt", "dest": "C:\\dst\\file2.txt"}
])
```

### PowerShell管理
```python
# 执行单次命令
ps_execute_command("Get-ChildItem", "C:\\Projects")

# 创建持久会话
session = ps_create_session("C:\\Projects")
ps_execute_command("$var = 'Hello'", "C:\\Projects", session_id=session["session_id"])
ps_execute_command("Write-Host $var", "C:\\Projects", session_id=session["session_id"])
```

### 下载文件
```python
# 单文件下载
download_files("https://example.com/file.zip", "file.zip", "C:\\Downloads")

# 批量下载
download_files(
    ["https://example.com/file1.zip", "https://example.com/file2.zip"],
    ["file1.zip", "file2.zip"],
    "C:\\Downloads"
)
```

### 系统监控
```python
# 获取基本系统信息（仅安全信息）
basic_info = system_get_basic_system_info()

# 获取完整系统信息（包含详细信息）
full_info = system_get_system_info()

# 获取系统信息（可选择详细程度）
system_info = system_get_system_info(basic_only=True)  # 仅基本信息
system_info = system_get_system_info(basic_only=False) # 详细信息

# 基本信息包含：
# - 操作系统、计算机名、处理器、频率
# - 显卡型号、显存、内存使用情况
# - IP地址、DNS服务器
# - Python和Node.js开发环境信息
```

## 安全特性

- **绝对路径强制**：所有路径参数必须使用绝对路径
- **PowerShell安全验证**：命令安全性检查和风险评估
- **文件类型验证**：下载文件的类型安全检查
- **路径验证**：防止路径遍历攻击

## 项目结构

```
ai-tool-mcp/
├── core/                   # 核心模块
│   ├── config.py          # 配置管理
│   ├── path_validator.py  # 路径验证
│   ├── security_validator.py # 安全验证
│   └── session_manager.py # 会话管理
├── services/              # 服务模块
│   ├── file_service.py    # 文件操作服务
│   ├── powershell_service.py # PowerShell管理服务
│   ├── download_service.py # 下载服务
│   └── system_service.py  # 系统监控服务
├── logs/                  # 日志文件
└── __main__.py           # 主入口
```

## 开发说明

### 添加新工具
1. 在对应服务文件中使用 `@self.tool()` 装饰器
2. 参数使用 `Annotated` 类型注解
3. 路径参数必须验证绝对路径格式

### 日志配置
日志文件位于 `logs/ai-tool.log`，支持按大小轮转。

## 许可证

MIT License
