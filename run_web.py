"""
图纸查询系统 - Web版本启动脚本
"""
import os
import sys
import socket
import subprocess
from app import app
from config import config

def find_available_port(start_port=5000, max_attempts=20):
    """查找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 连接到一个不存在的地址来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def check_and_open_firewall_port(port):
    """检查并尝试开放防火墙端口"""
    try:
        # 检查是否以管理员身份运行
        is_admin = subprocess.run(['net', 'session'], capture_output=True, text=True).returncode == 0
        
        if is_admin:
            # 尝试添加防火墙规则
            cmd = f'netsh advfirewall firewall add rule name="Flask Web App Port {port}" dir=in action=allow protocol=TCP localport={port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ 已自动开放防火墙端口 {port}")
                return True
            else:
                print(f"⚠️  防火墙端口开放失败，但程序将继续运行")
        else:
            print(f"💡 如需局域网访问，请以管理员身份运行或手动开放端口 {port}")
            print(f"   命令: netsh advfirewall firewall add rule name=\"Flask Web App Port {port}\" dir=in action=allow protocol=TCP localport={port}")
    except Exception as e:
        print(f"⚠️  防火墙配置检查失败: {e}")
    
    return False

def main():
    """启动Web应用"""
    print("=" * 60)
    print(f"🚀 启动 {config.APP_NAME} Web版本")
    print(f"📦 版本: {config.VERSION}")
    print(f"🌍 环境: {config.ENVIRONMENT}")
    print(f"📊 数据库: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
    print("=" * 60)
    
    # 检查templates目录
    if not os.path.exists('templates'):
        print("❌ 错误: templates目录不存在")
        sys.exit(1)
    
    # 检查数据库连接
    try:
        from database.db_manager import db_manager
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM drawings")
            count = cursor.fetchone()[0]
            cursor.close()
        print(f"✅ 数据库连接成功，共有 {count} 条图纸记录")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("请检查数据库配置和网络连接")
        sys.exit(1)
    
    # 查找可用端口
    port = find_available_port(5000, 20)
    if not port:
        print("❌ 无法找到可用端口，请检查网络配置")
        sys.exit(1)
    
    # 获取本机IP
    local_ip = get_local_ip()
    
    # 尝试自动配置防火墙
    firewall_ok = check_and_open_firewall_port(port)
    
    print("\n🌐 Web服务器启动信息:")
    print(f"   本地访问: http://localhost:{port}")
    print(f"   局域网访问: http://{local_ip}:{port}")
    
    if port != 5000:
        print(f"⚠️  注意: 5000端口被占用，已自动切换到端口 {port}")
    
    if not firewall_ok:
        print(f"⚠️  防火墙可能阻止外部访问，如需局域网访问请手动开放端口 {port}")
    
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    # 启动Flask应用
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=config.DEBUG,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"\n❌ 服务器启动失败: {e}")

if __name__ == '__main__':
    main()