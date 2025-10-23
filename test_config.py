"""
测试配置文件
"""
from config import config

print("=" * 60)
print("配置信息检查")
print("=" * 60)

print(f"应用名称: {config.APP_NAME}")
print(f"版本号: {config.VERSION}")
print()

print("数据库配置:")
print(f"  主机: {config.DB_HOST}")
print(f"  端口: {config.DB_PORT}")
print(f"  用户: {config.DB_USER}")
print(f"  密码: {'*' * len(config.DB_PASSWORD)}")  # 密码用*号隐藏
print(f"  数据库: {config.DB_NAME}")
print()

print("PDF路径配置:")
print(f"  网络路径: {config.PDF_NETWORK_PATH}")
print()

print("其他配置:")
print(f"  窗口尺寸: {config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
print(f"  调试模式: {config.DEBUG}")
print()

print("=" * 60)
print("✅ 配置文件加载成功！")
print("=" * 60)