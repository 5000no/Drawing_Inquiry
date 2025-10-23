"""
获取Web访问信息工具
显示当前可用的访问地址
"""
import socket
import subprocess
from config import config

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 方法1: 连接外部地址获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            # 方法2: 获取主机名对应IP
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            return "127.0.0.1"

def get_all_network_interfaces():
    """获取所有网络接口IP"""
    interfaces = []
    try:
        # 使用ipconfig命令获取网络信息
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='gbk')
        lines = result.stdout.split('\n')
        
        current_adapter = None
        for line in lines:
            line = line.strip()
            if '适配器' in line or 'adapter' in line.lower():
                current_adapter = line
            elif 'IPv4' in line and '192.168.' in line:
                # 提取IP地址
                ip = line.split(':')[-1].strip()
                if ip and ip != '127.0.0.1':
                    interfaces.append({
                        'adapter': current_adapter or 'Unknown',
                        'ip': ip
                    })
    except:
        # 如果命令失败，使用基本方法
        ip = get_local_ip()
        if ip != '127.0.0.1':
            interfaces.append({
                'adapter': 'Default',
                'ip': ip
            })
    
    return interfaces

def check_port_status(port):
    """检查端口是否被占用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            return False  # 端口可用
    except OSError:
        return True   # 端口被占用

def get_access_info():
    """获取完整的访问信息"""
    print("=" * 60)
    print("🌐 图纸查询系统 - Web访问信息")
    print("=" * 60)
    
    # 获取配置信息
    port = config.WEB_PORT
    fixed_ip = config.FIXED_LOCAL_IP
    
    print(f"📊 系统信息:")
    print(f"   应用名称: {config.APP_NAME}")
    print(f"   版本: {config.VERSION}")
    print(f"   环境: {config.ENVIRONMENT}")
    print(f"   配置端口: {port}")
    
    # 检查端口状态
    port_occupied = check_port_status(port)
    print(f"   端口状态: {'被占用' if port_occupied else '可用'}")
    
    print(f"\n🔗 访问地址:")
    
    # 本地访问
    print(f"   本机访问: http://localhost:{port}")
    
    # 获取网络接口
    interfaces = get_all_network_interfaces()
    
    if fixed_ip:
        # 使用固定IP
        print(f"   局域网访问: http://{fixed_ip}:{port} (固定IP)")
    else:
        # 显示所有可用IP
        if interfaces:
            print(f"   局域网访问:")
            for iface in interfaces:
                print(f"     http://{iface['ip']}:{port} ({iface['adapter']})")
        else:
            current_ip = get_local_ip()
            print(f"   局域网访问: http://{current_ip}:{port}")
    
    # 生成二维码链接（如果有的话）
    main_ip = fixed_ip if fixed_ip else get_local_ip()
    qr_url = f"http://{main_ip}:{port}"
    
    print(f"\n📱 移动设备访问:")
    print(f"   手机/平板: {qr_url}")
    print(f"   (确保设备连接同一WiFi网络)")
    
    # 防火墙提醒
    print(f"\n🔒 网络配置:")
    print(f"   如其他设备无法访问，请检查:")
    print(f"   1. Windows防火墙是否开放端口 {port}")
    print(f"   2. 路由器是否启用AP隔离")
    print(f"   3. 所有设备是否在同一网络")
    
    # 提供配置命令
    print(f"\n🛠️  防火墙配置命令:")
    print(f"   netsh advfirewall firewall add rule name=\"图纸查询系统\" dir=in action=allow protocol=TCP localport={port}")
    
    print("=" * 60)
    
    return {
        'port': port,
        'local_url': f"http://localhost:{port}",
        'network_url': qr_url,
        'interfaces': interfaces,
        'port_available': not port_occupied
    }

def save_access_info_to_file():
    """保存访问信息到文件"""
    info = get_access_info()
    
    # 生成访问信息文件
    content = f"""# 图纸查询系统 - 访问信息

## 🌐 当前访问地址

### 本机访问
```
{info['local_url']}
```

### 局域网访问
```
{info['network_url']}
```

### 所有可用地址
"""
    
    for iface in info['interfaces']:
        content += f"- http://{iface['ip']}:{info['port']} ({iface['adapter']})\n"
    
    content += f"""

## 📱 移动设备访问
确保手机/平板连接同一WiFi网络，然后访问：
```
{info['network_url']}
```

## 🔒 如果无法访问
1. 检查Windows防火墙设置
2. 以管理员身份运行以下命令：
```cmd
netsh advfirewall firewall add rule name="图纸查询系统" dir=in action=allow protocol=TCP localport={info['port']}
```

## 📋 系统信息
- 应用: {config.APP_NAME}
- 版本: {config.VERSION}
- 端口: {info['port']}
- 状态: {'运行中' if not info['port_available'] else '未启动'}
"""
    
    with open('当前访问地址.md', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n💾 访问信息已保存到: 当前访问地址.md")

if __name__ == '__main__':
    try:
        save_access_info_to_file()
        input("\n按回车键退出...")
    except KeyboardInterrupt:
        print("\n👋 已退出")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        input("按回车键退出...")