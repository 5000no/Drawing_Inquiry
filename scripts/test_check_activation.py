import os
import sys
import argparse

# 让脚本可以导入项目根目录的模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db_manager import db_manager


def check_code(code: str):
    ok = db_manager.check_activation_code(code)
    print(f"代码: {code} | 有效: {ok}")


def main():
    parser = argparse.ArgumentParser(description="校验激活码是否有效")
    parser.add_argument("code", nargs="?", help="要校验的激活码，可省略以批量校验数据库中的激活码")
    args = parser.parse_args()

    if args.code:
        check_code(args.code.strip().upper())
    else:
        codes = db_manager.get_all_activation_codes()
        print(f"共 {len(codes)} 个激活码，逐一校验有效性...")
        for item in codes:
            check_code(item["code"])


if __name__ == "__main__":
    main()