"""
图纸查询系统 - 配置文件
支持开发环境和生产环境切换
"""

class Config:
    """系统配置类"""
    
    # ==================== 基本信息 ====================
    APP_NAME = "图纸查询系统"
    VERSION = "1.1.0"
    
    # ==================== 环境切换 ====================
    # 'development': 开发环境（本地MySQL）
    # 'production': 生产环境（服务器MySQL）
    ENVIRONMENT = 'production'  # 👈 这里切换环境
    
    # ==================== 服务器配置 ====================
    SERVER_IP = "192.168.3.74"
    
    # ==================== MySQL数据库配置 ====================
    if ENVIRONMENT == 'development':
        # 开发环境：使用本地MySQL
        DB_HOST = "localhost"
        DB_PORT = 3306
        DB_USER = "root"
        DB_PASSWORD = "123456"  # 本地MySQL密码
        DB_NAME = "drawing_system"
        DB_CHARSET = "utf8mb4"
        print("🔧 当前环境: 开发环境 (本地MySQL)")
    else:
        # 生产环境：使用服务器MySQL
        DB_HOST = SERVER_IP
        DB_PORT = 3306
        DB_USER = "root"
        DB_PASSWORD = "123456"  # 服务器MySQL密码
        DB_NAME = "drawing_system"
        DB_CHARSET = "utf8mb4"
        print("🚀 当前环境: 生产环境 (服务器MySQL)")
    
    # ==================== PDF文件配置 ====================
    # PDF保存在本地
    PDF_NETWORK_PATH = "data/pdf/NR/"
    
    # ==================== 查询配置 ====================
    MAX_SEARCH_RESULTS = 100
    
    # ==================== 界面配置 ====================
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 700
    
    # ==================== Web服务器配置 ====================
    WEB_HOST = '0.0.0.0'  # 允许外部访问
    WEB_PORT = 5000       # 固定端口

    # 固定IP配置（可选，用于生成访问链接）
    FIXED_LOCAL_IP = None  # 如需固定IP，设置为具体IP如 '192.168.1.100'

    # ==================== 安全配置 ====================
    # 用于移动端令牌签名（HMAC），请在生产环境中替换为更安全的随机值
    SECRET_KEY = "change-this-to-a-strong-random-secret"
    MOBILE_TOKEN_EXP_SECONDS = 7 * 24 * 3600

    # ==================== 日志配置 ====================
    ENABLE_LOGGING = True
    LOG_DIR = "data/logs"
    
    # ==================== 开发模式 ====================
    DEBUG = True if ENVIRONMENT == 'development' else False


# 创建全局配置实例
config = Config()

