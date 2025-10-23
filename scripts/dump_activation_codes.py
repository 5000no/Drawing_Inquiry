import json
import os
import sys

# 确保可以从项目根目录导入 database 包
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db_manager import db_manager


def serialize_codes(codes):
    for d in codes:
        ca = d.get("created_at")
        if ca is not None:
            # 使用 ISO 8601 格式输出时间
            try:
                d["created_at"] = ca.isoformat()
            except Exception:
                d["created_at"] = str(ca)
    return codes


def main():
    codes = db_manager.get_all_activation_codes()
    codes = serialize_codes(codes)
    print(json.dumps(codes, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()