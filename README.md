# AI-Tool MCP

基于FastMCP的AI工具集合，提供文件操作、系统监控和下载功能。

**🎯 总计15个工具，功能完整，架构清晰**

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

## 安装配置

### 环境要求
- **Python**: 3.8+ (推荐3.12+)
- **操作系统**: Windows 10/11 (PowerShell功能需要)
- **PowerShell**: 7.x (自动检测，回退到5.1)

### 安装依赖
```bash
# 安装核心依赖
pip install fastmcp requests psutil validators aiofiles

# 或使用项目目录安装
cd ai-tool-mcp
pip install -r requirements.txt  # 如果有requirements.txt
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

## 🔒 安全特性

- **绝对路径强制**: 所有路径参数必须使用绝对路径，防止相对路径攻击
- **PowerShell安全验证**: 命令安全性检查和风险评估，阻止危险操作
- **文件类型验证**: 下载文件的类型安全检查，支持白名单机制
- **路径验证**: 防止路径遍历攻击，确保操作在允许范围内
- **会话隔离**: PowerShell会话独立管理，避免相互干扰

## 📁 项目结构

```
ai-tool-mcp/
├── core/                   # 核心模块
│   ├── __init__.py        # 核心初始化
│   ├── config.py          # 配置管理
│   ├── file_downloader.py # 文件下载器
│   ├── file_option.py     # 文件操作
│   ├── path_validator.py  # 路径验证
│   └── system_monitor.py  # 系统监控
├── services/              # 服务模块
│   ├── base_service.py    # 基础服务类
│   ├── file_service.py    # 文件操作服务
│   ├── download_service.py # 下载服务
│   └── system_service.py  # 系统监控服务
├── tests/                 # 测试文件
├── logs/                  # 日志文件（自动创建）
├── server.py             # 主服务器入口
├── mcp.json              # MCP配置
└── pyproject.toml        # 项目配置
```

## 🛠️ 开发说明

### 添加新工具
1. 在对应服务文件中使用 `@self.tool()` 装饰器
2. 参数使用 `Annotated[type, Field(description="...")]` 类型注解
3. 路径参数必须验证绝对路径格式
4. 异步函数使用 `async def`，同步函数直接定义

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
| **总计** | **15个** | **功能完整的AI工具集** |

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
