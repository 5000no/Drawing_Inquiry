import os
import sys

# 让脚本可以导入项目根目录的模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pymysql
from database.db_manager import db_manager


def main():
    updated = 0
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        try:
            # 尝试更新新列名
            cur.execute("UPDATE activation_codes SET is_active = TRUE")
            updated = cur.rowcount
        except Exception as e:
            if "Unknown column 'is_active'" in str(e):
                # 兼容旧库列名
                cur.execute("UPDATE activation_codes SET is_activated = TRUE")
                updated = cur.rowcount
            else:
                raise
        conn.commit()
        cur.close()
    print(f"✅ 已激活激活码数量: {updated}")


if __name__ == "__main__":
    main()