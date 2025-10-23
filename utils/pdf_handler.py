"""
PDF文件处理器
负责打开、验证PDF文件
"""
import os
import subprocess
import platform
from config import config


class PDFHandler:
    """PDF文件处理器"""
    
    def __init__(self):
        """初始化"""
        self.pdf_root = config.PDF_NETWORK_PATH
        if config.DEBUG:
            print(f"📂 PDF根目录: {self.pdf_root}")
    
    def get_full_path(self, pdf_path, activation_code=None):
        """
        获取PDF完整路径
        
        参数:
            pdf_path: PDF相对路径（如：NR1001.pdf）
            activation_code: 激活码（可选）
        
        返回:
            str: 完整路径
        """
        from utils.activation_code import ActivationCodeManager
        
        # 如果提供了激活码，则使用激活码对应的子文件夹
        if activation_code:
            try:
                # 获取激活码对应的文件夹名
                folder_name = ActivationCodeManager.get_folder_name(activation_code)
                
                # 确保文件夹存在
                folder_path = os.path.join(self.pdf_root, folder_name)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path, exist_ok=True)
                    if config.DEBUG:
                        print(f"📂 创建激活码文件夹: {folder_path}")
                
                # 拼接完整路径
                full_path = os.path.join(folder_path, pdf_path)
                return full_path
            except Exception as e:
                if config.DEBUG:
                    print(f"❌ 获取激活码文件夹失败: {e}")
                # 如果获取激活码文件夹失败，则使用默认路径
        
        # 拼接完整路径（默认路径）
        full_path = os.path.join(self.pdf_root, pdf_path)
        return full_path
    
    def check_exists(self, pdf_path, activation_code=None):
        """
        检查PDF文件是否存在
        
        参数:
            pdf_path: PDF相对路径
            activation_code: 激活码（可选）
        
        返回:
            tuple: (是否存在, 完整路径)
        """
        full_path = self.get_full_path(pdf_path, activation_code)
        exists = os.path.exists(full_path)
        
        if config.DEBUG:
            if exists:
                print(f"✅ PDF文件存在: {full_path}")
            else:
                print(f"❌ PDF文件不存在: {full_path}")
        
        return (exists, full_path)
    
    def open_pdf(self, pdf_path, activation_code=None):
        """
        打开PDF文件
        
        参数:
            pdf_path: PDF相对路径（如：NR1001.pdf）
            activation_code: 激活码（可选）
        
        返回:
            tuple: (是否成功, 消息)
        """
        # 获取完整路径
        full_path = self.get_full_path(pdf_path, activation_code)
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            error_msg = f"PDF文件不存在！\n路径: {full_path}"
            return (False, error_msg)
        
        # 检查是否是PDF文件
        if not full_path.lower().endswith('.pdf'):
            error_msg = "文件不是PDF格式！"
            return (False, error_msg)
        
        # 打开PDF文件
        try:
            system = platform.system()
            
            if system == 'Windows':
                # Windows系统：使用系统默认程序打开
                os.startfile(full_path)
                
            elif system == 'Darwin':
                # macOS系统
                subprocess.Popen(['open', full_path])
                
            else:
                # Linux系统
                subprocess.Popen(['xdg-open', full_path])
            
            if config.DEBUG:
                print(f"✅ 已打开PDF: {full_path}")
            
            return (True, f"已打开: {pdf_path}")
            
        except Exception as e:
            error_msg = f"打开PDF失败: {str(e)}"
            print(f"❌ {error_msg}")
            return (False, error_msg)
    
    def open_pdf_folder(self):
        """
        打开PDF根目录文件夹
        
        返回:
            tuple: (是否成功, 消息)
        """
        try:
            if os.path.exists(self.pdf_root):
                os.startfile(self.pdf_root)
                return (True, "已打开PDF文件夹")
            else:
                return (False, f"PDF目录不存在: {self.pdf_root}")
        except Exception as e:
            return (False, f"打开失败: {str(e)}")


# 创建全局实例
pdf_handler = PDFHandler()