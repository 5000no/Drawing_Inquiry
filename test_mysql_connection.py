"""
测试MySQL连接
逐步诊断连接问题
"""
import pymysql
from config import config

print("=" * 60)
print("MySQL连接诊断")
print("=" * 60)

# 测试1: 网络连通性
print("\n[测试1] 检查网络连通性...")
import os
response = os.system(f"ping -n 1 {config.DB_HOST} > nul")
if response == 0:
    print(f"✅ 网络连通: {config.DB_HOST} 可以ping通")
else:
    print(f"❌ 网络不通: {config.DB_HOST} ping不通")
    print("  解决方案: 检查服务器IP是否正确，网络是否连接")
    exit(1)

# 测试2: 端口连通性
print("\n[测试2] 检查MySQL端口...")
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(3)
result = sock.connect_ex((config.DB_HOST, config.DB_PORT))
sock.close()

if result == 0:
    print(f"✅ 端口开放: {config.DB_HOST}:{config.DB_PORT} 可访问")
else:
    print(f"❌ 端口不通: {config.DB_HOST}:{config.DB_PORT} 无法访问")
    print("  可能原因:")
    print("    1. MySQL服务未启动")
    print("    2. 防火墙阻止了3306端口")
    print("    3. MySQL未配置允许远程连接")
    exit(1)

# 测试3: MySQL连接
print("\n[测试3] 尝试连接MySQL...")
try:
    connection = pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        charset=config.DB_CHARSET,
        connect_timeout=10  # 增加超时时间
    )
    print("✅ MySQL连接成功！")
    
    # 测试查询
    cursor = connection.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"✅ MySQL版本: {version[0]}")
    
    cursor.execute("SELECT USER()")
    user = cursor.fetchone()
    print(f"✅ 当前用户: {user[0]}")
    
    cursor.close()
    connection.close()
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！MySQL连接正常！")
    print("=" * 60)
    
except pymysql.err.OperationalError as e:
    print(f"❌ MySQL连接失败: {e}")
    print("\n可能的原因:")
    if "Access denied" in str(e):
        print("  - 用户名或密码错误")
        print("  - 检查config.py中的DB_USER和DB_PASSWORD")
    elif "Can't connect" in str(e):
        print("  - MySQL服务未启动")
        print("  - 防火墙阻止连接")
    elif "Lost connection" in str(e):
        print("  - MySQL配置问题")
        print("  - 需要配置允许远程连接")
    exit(1)
    
except Exception as e:
    print(f"❌ 未知错误: {e}")
    exit(1)