# 创建一个测试文件 test_install.py
# 复制以下内容

print("正在检查依赖包...")

try:
    import PyQt5
    print("✅ PyQt5: OK")
except ImportError as e:
    print(f"❌ PyQt5: {e}")

try:
    import pymysql
    print("✅ pymysql: OK")
except ImportError as e:
    print(f"❌ pymysql: {e}")

try:
    import sqlalchemy
    print("✅ SQLAlchemy: OK")
except ImportError as e:
    print(f"❌ SQLAlchemy: {e}")

try:
    import cryptography
    print("✅ cryptography: OK")
except ImportError as e:
    print(f"❌ cryptography: {e}")

try:
    import pandas
    print("✅ pandas: OK")
except ImportError as e:
    print(f"❌ pandas: {e}")

try:
    import openpyxl
    print("✅ openpyxl: OK")
except ImportError as e:
    print(f"❌ openpyxl: {e}")

try:
    import PyInstaller
    print("✅ PyInstaller: OK")
except ImportError as e:
    print(f"❌ PyInstaller: {e}")

print("\n" + "="*50)
print("依赖检查完成！")