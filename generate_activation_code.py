"""
激活码生成工具
用于生成激活码并添加到数据库
"""
import os
import sys
import argparse
from utils.activation_code import ActivationCodeManager
from database.db_manager import DatabaseManager
from config import config

def generate_codes(count, description_prefix="", output_file=None):
    """
    生成指定数量的激活码
    
    参数:
        count: 生成数量
        description_prefix: 描述前缀
        output_file: 输出文件路径
    
    返回:
        list: 生成的激活码列表
    """
    db_manager = DatabaseManager()
    codes = []
    
    print(f"开始生成 {count} 个激活码...")
    
    for i in range(count):
        # 生成激活码
        code = ActivationCodeManager.generate_code()
        description = f"{description_prefix}#{i+1}" if description_prefix else f"激活码#{i+1}"
        
        # 添加到数据库
        success = db_manager.add_activation_code(code, description)
        
        if success:
            codes.append(code)
            print(f"✅ [{i+1}/{count}] 生成激活码: {code}")
            
            # 创建激活码对应的文件夹
            folder_name = ActivationCodeManager.get_folder_name(code)
            folder_path = os.path.join(config.PDF_NETWORK_PATH, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                print(f"📂 创建文件夹: {folder_path}")
        else:
            print(f"❌ [{i+1}/{count}] 激活码生成失败，重试...")
            i -= 1  # 重试
    
    # 保存到文件
    if output_file:
        try:
            with open(output_file, 'w') as f:
                for code in codes:
                    f.write(f"{code}\n")
            print(f"✅ 已将激活码保存到文件: {output_file}")
        except Exception as e:
            print(f"❌ 保存到文件失败: {e}")
    
    return codes

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="激活码生成工具")
    parser.add_argument("-c", "--count", type=int, default=1, help="生成激活码数量")
    parser.add_argument("-p", "--prefix", type=str, default="", help="描述前缀")
    parser.add_argument("-o", "--output", type=str, default="activation_codes.txt", help="输出文件路径")
    
    args = parser.parse_args()
    
    # 生成激活码
    codes = generate_codes(args.count, args.prefix, args.output)
    
    print(f"\n✅ 成功生成 {len(codes)} 个激活码")
    print(f"📝 激活码已保存到: {args.output}")

if __name__ == "__main__":
    main()