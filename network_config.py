"""
网络配置工具 - 解决局域网访问问题
提供多种代码层面的解决方案
"""
import socket
import subprocess
import sys
import os
from contextlib import contextmanager

class NetworkConfig:
    """网络配置管理器"""
    
    def __init__(self):
        self.available_ports = []
        self.local_ip = self.get_local_ip()
        
    def get_local_ip(self):
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
    
    def find_available_ports(self, start_port=5000, count=10):
        """查找多个可用端口"""
        available = []
        for port in range(start_port, start_port + 100):
            if len(available) >= count:
                break
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    available.append(port)
            except OSError:
                continue
        return available
    
    def check_port_accessibility(self, port, timeout=3):
        """检查端口是否可从外部访问"""
        try:
            # 尝试从本机连接到自己的端口
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                result = s.connect_ex((self.local_ip, port))
                return result == 0
        except:
            return False
    
    def is_admin(self):
        """检查是否有管理员权限"""
        try:
            return subprocess.run(['net', 'session'], 
                                capture_output=True, text=True).returncode == 0
        except:
            return False
    
    def add_firewall_rule(self, port, rule_name=None):
        """添加防火墙规则"""
        if not rule_name:
            rule_name = f"Flask Web App Port {port}"
        
        try:
            cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=in action=allow protocol=TCP localport={port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stderr
        except Exception as e:
            return False, str(e)
    
    def remove_firewall_rule(self, rule_name):
        """删除防火墙规则"""
        try:
            cmd = f'netsh advfirewall firewall delete rule name="{rule_name}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def check_firewall_rule_exists(self, port):
        """检查防火墙规则是否存在"""
        try:
            cmd = f'netsh advfirewall firewall show rule name=all | findstr {port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return str(port) in result.stdout
        except:
            return False
    
    def get_network_interfaces(self):
        """获取网络接口信息"""
        interfaces = []
        try:
            import psutil
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                        interfaces.append({
                            'interface': interface,
                            'ip': addr.address,
                            'netmask': addr.netmask
                        })
        except ImportError:
            # 如果没有psutil，使用基本方法
            interfaces.append({
                'interface': 'default',
                'ip': self.local_ip,
                'netmask': '255.255.255.0'
            })
        return interfaces
    
    def auto_configure(self, preferred_port=5000):
        """自动配置网络访问"""
        print("🔧 开始自动网络配置...")
        
        # 1. 查找可用端口
        if self.is_port_available(preferred_port):
            port = preferred_port
            print(f"✅ 端口 {port} 可用")
        else:
            available_ports = self.find_available_ports(preferred_port, 5)
            if not available_ports:
                print("❌ 无法找到可用端口")
                return None
            port = available_ports[0]
            print(f"⚠️  端口 {preferred_port} 被占用，使用端口 {port}")
        
        # 2. 检查管理员权限
        if self.is_admin():
            print("✅ 检测到管理员权限")
            
            # 3. 配置防火墙
            if not self.check_firewall_rule_exists(port):
                success, error = self.add_firewall_rule(port)
                if success:
                    print(f"✅ 已自动开放防火墙端口 {port}")
                else:
                    print(f"⚠️  防火墙配置失败: {error}")
            else:
                print(f"✅ 防火墙端口 {port} 已开放")
        else:
            print("⚠️  未检测到管理员权限")
            print(f"💡 手动开放端口命令: netsh advfirewall firewall add rule name=\"Flask Web App Port {port}\" dir=in action=allow protocol=TCP localport={port}")
        
        # 4. 显示访问信息
        print(f"\n🌐 网络配置完成:")
        print(f"   本地访问: http://localhost:{port}")
        print(f"   局域网访问: http://{self.local_ip}:{port}")
        
        # 5. 显示所有网络接口
        interfaces = self.get_network_interfaces()
        if len(interfaces) > 1:
            print(f"\n📡 所有可用网络接口:")
            for iface in interfaces:
                print(f"   {iface['interface']}: http://{iface['ip']}:{port}")
        
        return port
    
    def is_port_available(self, port):
        """检查端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except OSError:
            return False
    
    @contextmanager
    def temporary_firewall_rule(self, port):
        """临时防火墙规则上下文管理器"""
        rule_name = f"Temp Flask Web App Port {port}"
        added = False
        
        try:
            if self.is_admin():
                success, _ = self.add_firewall_rule(port, rule_name)
                if success:
                    added = True
                    print(f"✅ 临时开放端口 {port}")
            
            yield port
            
        finally:
            if added:
                if self.remove_firewall_rule(rule_name):
                    print(f"✅ 已清理临时防火墙规则")

def main():
    """主函数 - 网络配置工具"""
    config = NetworkConfig()
    
    print("=" * 50)
    print("🌐 网络配置工具")
    print("=" * 50)
    
    print(f"🖥️  本机IP: {config.local_ip}")
    print(f"👑 管理员权限: {'是' if config.is_admin() else '否'}")
    
    # 查找可用端口
    available_ports = config.find_available_ports(5000, 5)
    print(f"🔌 可用端口: {available_ports}")
    
    # 显示网络接口
    interfaces = config.get_network_interfaces()
    print(f"\n📡 网络接口:")
    for iface in interfaces:
        print(f"   {iface['interface']}: {iface['ip']}")
    
    # 自动配置
    print(f"\n🔧 自动配置结果:")
    port = config.auto_configure(5000)
    
    if port:
        print(f"\n✅ 配置完成！推荐使用端口 {port}")
    else:
        print(f"\n❌ 配置失败，请手动配置")

if __name__ == '__main__':
    main()