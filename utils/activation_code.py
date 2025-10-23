"""
激活码管理模块
负责生成、验证和管理激活码
"""
import uuid
import time
import hashlib
import re
import os
from config import config

class ActivationCodeManager:
    """激活码管理器"""
    
    # 激活码前缀
    PREFIX = "VB-"
    
    @staticmethod
    def generate_code(description=""):
        """
        生成新的激活码
        
        参数:
            description: 激活码描述（可选）
            
        返回:
            str: 生成的激活码
        """
        # 生成UUID部分
        uuid_part = str(uuid.uuid4()).replace('-', '')[:12].upper()
        
        # 添加时间戳哈希（防止猜测）
        timestamp = int(time.time())
        time_hash = hashlib.md5(f"{timestamp}".encode()).hexdigest()[:4].upper()
        
        # 组合激活码
        activation_code = f"{ActivationCodeManager.PREFIX}{uuid_part}-{time_hash}"
        
        return activation_code
    
    @staticmethod
    def validate_code_format(code):
        """
        验证激活码格式是否正确
        
        参数:
            code: 待验证的激活码
            
        返回:
            bool: 格式正确返回True，否则返回False
        """
        # 验证格式: VB-XXXXXXXXXXXX-XXXX
        pattern = r'^VB-[A-Z0-9]{12}-[A-Z0-9]{4}$'
        return bool(re.match(pattern, code))
    
    @staticmethod
    def get_folder_name(code):
        """
        从激活码获取对应的文件夹名称
        
        参数:
            code: 激活码
            
        返回:
            str: 文件夹名称
        """
        if not ActivationCodeManager.validate_code_format(code):
            raise ValueError("激活码格式不正确")
        
        # 使用激活码的UUID部分作为文件夹名
        folder_name = code.split('-')[1]
        return folder_name
    
    @staticmethod
    def ensure_folder_exists(code):
        """
        确保激活码对应的文件夹存在
        
        参数:
            code: 激活码
            
        返回:
            str: 创建的文件夹路径
        """
        folder_name = ActivationCodeManager.get_folder_name(code)
        folder_path = os.path.join(config.PDF_NETWORK_PATH, folder_name)
        
        # 确保文件夹存在
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
            
        return folder_path