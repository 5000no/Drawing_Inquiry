"""
测试数据库管理器
"""
from database.db_manager import db_manager

print("=" * 60)
print("测试数据库管理器")
print("=" * 60)

# 测试1: 精确查询
print("\n[测试1] 精确查询 NR1001...")
result = db_manager.search_by_code('NR1001')
if result:
    print(f"✅ 找到图纸:")
    print(f"   ID: {result['id']}")
    print(f"   产品号: {result['product_code']}")
    print(f"   PDF路径: {result['pdf_path']}")
else:
    print("❌ 未找到")

# 测试2: 模糊查询
print("\n[测试2] 模糊查询 'NR'...")
results = db_manager.search_fuzzy('NR')
print(f"✅ 找到 {len(results)} 条记录:")
for r in results:
    print(f"   - {r['product_code']}: {r['pdf_path']}")

# 测试3: 获取总数
print("\n[测试3] 获取图纸总数...")
count = db_manager.get_total_count()
print(f"✅ 图纸总数: {count}")

# 测试4: 添加图纸
print("\n[测试4] 添加新图纸 NR1003...")
success = db_manager.add_drawing('NR1003', 'NR1003.pdf')
if success:
    print("✅ 添加成功")
    # 验证
    result = db_manager.search_by_code('NR1003')
    print(f"   验证: {result['product_code']}")
else:
    print("❌ 添加失败")

# 测试5: 统计
print("\n[测试5] 最新统计...")
count = db_manager.get_total_count()
print(f"✅ 当前图纸总数: {count}")

print("\n" + "=" * 60)
print("🎉 数据库管理器测试完成！")
print("=" * 60)