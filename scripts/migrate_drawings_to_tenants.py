import os
import sys

# 让脚本可以导入项目根目录的模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pymysql
from database.db_manager import db_manager


def main():
    print("🚚 开始迁移图纸数据到各租户数据库（按激活码）...")
    total = 0
    migrated = 0
    skipped = 0
    tenants = {}

    # 从主库读取所有图纸（需包含 activation_code 列）
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("SELECT product_code, pdf_path, activation_code FROM drawings")
        except Exception as e:
            print(f"❌ 主库 drawings 表不包含 activation_code 列，无法自动迁移: {e}")
            return
        rows = cur.fetchall()
        cur.close()

    total = len(rows)
    print(f"📊 主库共 {total} 条图纸记录")

    # 按激活码分组
    from collections import defaultdict
    grouped = defaultdict(list)
    for product_code, pdf_path, activation_code in rows:
        if not activation_code:
            skipped += 1
            continue
        grouped[activation_code].append((product_code, pdf_path))

    # 迁移到各租户库
    for code, items in grouped.items():
        tenant_db = db_manager.ensure_tenant_database(code)
        tenants[code] = tenant_db
        with db_manager.get_tenant_connection(activation_code=code) as tconn:
            tcur = tconn.cursor()
            for product_code, pdf_path in items:
                try:
                    tcur.execute(
                        "INSERT INTO drawings (product_code, pdf_path) VALUES (%s, %s)",
                        (product_code, pdf_path)
                    )
                    migrated += 1
                except pymysql.IntegrityError:
                    skipped += 1
            tcur.close()

    print("✅ 迁移完成")
    print(f"  • 成功迁移: {migrated}")
    print(f"  • 跳过/重复或无激活码: {skipped}")
    print(f"  • 涉及租户: {len(tenants)} 个")


if __name__ == "__main__":
    main()