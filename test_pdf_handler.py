"""
测试PDF处理模块
"""
from utils.pdf_handler import pdf_handler

print("=" * 60)
print("测试PDF处理模块")
print("=" * 60)

# 测试1: 获取完整路径
print("\n[测试1] 获取PDF完整路径...")
full_path = pdf_handler.get_full_path('NR1001.pdf')
print(f"✅ 完整路径: {full_path}")

# 测试2: 检查文件是否存在
print("\n[测试2] 检查NR1001.pdf是否存在...")
exists, path = pdf_handler.check_exists('NR1001.pdf')
if exists:
    print(f"✅ 文件存在: {path}")
else:
    print(f"❌ 文件不存在: {path}")

print("\n[测试3] 检查NR1002.pdf是否存在...")
exists, path = pdf_handler.check_exists('NR1002.pdf')
if exists:
    print(f"✅ 文件存在: {path}")
else:
    print(f"❌ 文件不存在: {path}")

print("\n[测试4] 检查不存在的文件...")
exists, path = pdf_handler.check_exists('NR9999.pdf')
if exists:
    print(f"✅ 文件存在: {path}")
else:
    print(f"❌ 文件不存在: {path}")

# 测试5: 打开PDF（这个会真的打开文件）
print("\n[测试5] 尝试打开 NR1001.pdf...")
print("提示: 这将使用系统默认PDF阅读器打开文件")
input("按回车键继续...")

success, msg = pdf_handler.open_pdf('NR1001.pdf')
if success:
    print(f"✅ {msg}")
else:
    print(f"❌ {msg}")

print("\n" + "=" * 60)
print("🎉 PDF处理模块测试完成！")
print("=" * 60)