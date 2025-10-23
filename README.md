# 图纸查询系统 - Web版本

## 概述

这是图纸查询系统的Web版本，将原有的PyQt5桌面应用转换为基于Flask的Web应用，保持了所有核心功能的同时提供了更好的跨平台兼容性和远程访问能力。

## 功能特性

- ✅ **精确查询**: 通过产品号精确查找图纸
- ✅ **模糊搜索**: 支持关键词模糊搜索
- ✅ **PDF在线预览**: 直接在浏览器中查看PDF文件
- ✅ **响应式设计**: 支持桌面和移动设备
- ✅ **现代化界面**: 使用Bootstrap 5构建美观界面
- ✅ **数据库复用**: 完全兼容现有MySQL数据库
- ✅ **配置管理**: 支持开发/生产环境切换

## 技术架构

### 后端
- **框架**: Flask 2.3.3
- **数据库**: MySQL (复用现有数据库)
- **ORM**: 直接使用PyMySQL
- **文件服务**: Flask静态文件服务

### 前端
- **UI框架**: Bootstrap 5.3.0
- **图标**: Font Awesome 6.4.0
- **PDF查看**: 浏览器原生PDF查看器
- **交互**: 原生JavaScript (无需额外框架)

## 安装和运行

### 1. 安装依赖

```bash
# 安装Web版本依赖
pip install -r web_requirements.txt
```

### 2. 配置检查

确保 `config.py` 中的数据库配置正确：

```python
# 数据库配置
DB_HOST = "192.168.3.74"  # 或你的数据库服务器IP
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "123456"
DB_NAME = "drawing_system"
```

### 3. 启动Web服务器

```bash
# 方式1: 使用启动脚本 (推荐)
python run_web.py

# 方式2: 直接运行Flask应用
python app.py
```

### 4. 访问应用

- **本地访问**: http://localhost:5000
- **局域网访问**: http://你的IP地址:5000

## 文件结构

```
项目根目录/
├── app.py                 # Flask主应用文件
├── run_web.py            # Web启动脚本
├── web_requirements.txt  # Web版本依赖
├── templates/            # HTML模板目录
│   └── index.html       # 主页面模板
├── config.py            # 配置文件 (复用)
├── database/            # 数据库模块 (复用)
│   └── db_manager.py
└── utils/               # 工具模块 (复用)
    └── pdf_handler.py
```

## API接口

### 1. 精确搜索
- **URL**: `/api/search`
- **方法**: POST
- **参数**: `{"product_code": "NR1001"}`
- **返回**: 图纸详细信息

### 2. 模糊搜索
- **URL**: `/api/search/fuzzy`
- **方法**: POST
- **参数**: `{"keyword": "NR", "limit": 20}`
- **返回**: 匹配的图纸列表

### 3. PDF文件服务
- **URL**: `/api/pdf/<drawing_id>`
- **方法**: GET
- **返回**: PDF文件流

### 4. 统计信息
- **URL**: `/api/statistics`
- **方法**: GET
- **返回**: 系统统计信息

## 部署建议

### 开发环境
使用内置的Flask开发服务器：
```bash
python run_web.py
```

### 生产环境
推荐使用Gunicorn + Nginx：

```bash
# 安装Gunicorn
pip install gunicorn

# 启动Gunicorn服务器
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 与桌面版本的对比

| 特性 | 桌面版 (PyQt5) | Web版 (Flask) |
|------|----------------|---------------|
| 跨平台 | Windows主要 | 全平台浏览器 |
| 部署 | 需要安装exe | 浏览器访问 |
| 界面 | 原生桌面UI | 现代Web UI |
| PDF查看 | 系统默认程序 | 浏览器内嵌 |
| 远程访问 | 不支持 | 支持 |
| 移动设备 | 不支持 | 响应式支持 |
| 数据库 | 完全兼容 | 完全兼容 |

## 注意事项

1. **PDF文件访问**: 确保Web服务器能够访问PDF文件所在的网络路径
2. **防火墙设置**: 如需局域网访问，请开放5000端口
3. **数据库连接**: 确保数据库服务器允许Web服务器的连接
4. **文件权限**: 确保Web应用有读取PDF文件的权限

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务器是否运行
   - 验证连接参数是否正确
   - 确认网络连通性

2. **PDF文件无法显示**
   - 检查PDF文件路径是否正确
   - 验证文件权限设置
   - 确认网络共享访问权限

3. **页面无法访问**
   - 检查防火墙设置
   - 验证端口是否被占用
   - 确认服务器启动状态

## 更新日志

- **v1.1.0-web**: 初始Web版本发布
  - 完整的Web界面实现
  - 所有核心功能迁移完成
  - 响应式设计支持
  - PDF在线预览功能
