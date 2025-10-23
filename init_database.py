"""
数据库初始化脚本
用于创建数据库、表结构、插入测试数据
"""
import pymysql
from config import config

def init_database():
    """初始化数据库"""
    
    print("=" * 60)
    print("开始初始化数据库...")
    print("=" * 60)
    
    try:
        # ========== 步骤1: 连接MySQL（不指定数据库） ==========
        print("\n[1/4] 正在连接MySQL服务器...")
        connection = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            charset=config.DB_CHARSET
        )
        print("✅ MySQL服务器连接成功！")
        
        cursor = connection.cursor()
        
        # ========== 步骤2: 创建数据库 ==========
        print("\n[2/4] 正在创建数据库...")
        
        # 先删除旧数据库（如果存在）
        cursor.execute(f"DROP DATABASE IF EXISTS {config.DB_NAME}")
        print(f"  - 已删除旧数据库（如果存在）")
        
        # 创建新数据库
        cursor.execute(f"""
            CREATE DATABASE {config.DB_NAME} 
            CHARACTER SET utf8mb4 
            COLLATE utf8mb4_unicode_ci
        """)
        print(f"✅ 数据库 '{config.DB_NAME}' 创建成功！")
        
        # 使用该数据库
        cursor.execute(f"USE {config.DB_NAME}")
        
        # ========== 步骤3: 创建表（简化版） ==========
        print("\n[3/4] 正在创建数据表...")
        
        # 创建激活码表
        create_activation_codes_table = """
        CREATE TABLE activation_codes (
            code VARCHAR(100) PRIMARY KEY COMMENT '激活码（主键）',
            description VARCHAR(255) COMMENT '激活码描述',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            is_activated BOOLEAN DEFAULT FALSE COMMENT '是否已激活'
        ) ENGINE=InnoDB 
          DEFAULT CHARSET=utf8mb4 
          COLLATE=utf8mb4_unicode_ci 
          COMMENT='激活码表'
        """
        cursor.execute(create_activation_codes_table)
        print("✅ 数据表 'activation_codes' 创建成功！")
        
        # 创建用户表
        create_users_table = """
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
            username VARCHAR(100) NOT NULL UNIQUE COMMENT '用户名',
            password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
            email VARCHAR(255) COMMENT '邮箱',
            activation_code VARCHAR(100) NOT NULL COMMENT '激活码',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            last_login DATETIME COMMENT '最后登录时间',
            is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
            FOREIGN KEY (activation_code) REFERENCES activation_codes(code) ON DELETE CASCADE
        ) ENGINE=InnoDB 
          DEFAULT CHARSET=utf8mb4 
          COLLATE=utf8mb4_unicode_ci 
          COMMENT='用户表'
        """
        cursor.execute(create_users_table)
        print("✅ 数据表 'users' 创建成功！")
        
        # 创建图纸表
        create_table_sql = """
        CREATE TABLE drawings (
            -- 核心字段
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID，自动递增',
            product_code VARCHAR(100) NOT NULL UNIQUE COMMENT '产品号（唯一标识）',
            pdf_path VARCHAR(500) NOT NULL COMMENT 'PDF文件路径',
            activation_code VARCHAR(100) COMMENT '关联的激活码',
            
            -- 后续可扩展字段（预留，暂时不用）
            -- product_name VARCHAR(255) COMMENT '产品名称',
            -- specifications TEXT COMMENT '规格参数',
            -- category VARCHAR(50) COMMENT '产品类别',
            -- status ENUM('Active', 'Archived') DEFAULT 'Active' COMMENT '状态',
            -- create_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            -- remark TEXT COMMENT '备注',
            
            -- 索引：加快查询速度
            INDEX idx_product_code (product_code),
            
            -- 外键约束
            FOREIGN KEY (activation_code) REFERENCES activation_codes(code) ON DELETE SET NULL
        ) ENGINE=InnoDB 
          DEFAULT CHARSET=utf8mb4 
          COLLATE=utf8mb4_unicode_ci 
          COMMENT='图纸信息表'
        """
        
        cursor.execute(create_table_sql)
        print("✅ 数据表 'drawings' 创建成功！")
        print("  表结构:")
        print("    - id: 主键，自动递增")
        print("    - product_code: 产品号（唯一）")
        print("    - pdf_path: PDF文件路径")
        print("    - activation_code: 关联的激活码")
        
        # ========== 步骤4: 插入测试数据 ==========
        print("\n[4/4] 正在插入测试数据...")
        
        test_data = [
            ('NR1001', 'NR1001.pdf'),
            ('NR1002', 'NR1002.pdf')
        ]
        
        insert_sql = """
        INSERT INTO drawings (product_code, pdf_path)
        VALUES (%s, %s)
        """
        
        cursor.executemany(insert_sql, test_data)
        connection.commit()
        
        print(f"✅ 成功插入 {len(test_data)} 条测试数据！")
        
        # ========== 验证数据 ==========
        print("\n" + "=" * 60)
        print("数据验证:")
        print("=" * 60)
        
        cursor.execute("SELECT COUNT(*) FROM drawings")
        count = cursor.fetchone()[0]
        print(f"数据表记录数: {count}")
        
        cursor.execute("SELECT id, product_code, pdf_path FROM drawings")
        results = cursor.fetchall()
        print("\n已插入的数据:")
        print(f"{'ID':<5} {'产品号':<15} {'PDF路径'}")
        print("-" * 60)
        for row in results:
            print(f"{row[0]:<5} {row[1]:<15} {row[2]}")
        
        # ========== 完成 ==========
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 60)
        print("🎉 数据库初始化完成！")
        print("=" * 60)
        print("\n提示:")
        print("  - 后续如需添加字段，请取消注释预留字段")
        print("  - 或参考注释格式添加新字段")
        return True
        
    except pymysql.Error as e:
        print(f"\n❌ 数据库操作失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        return False


if __name__ == '__main__':
    # 执行初始化
    init_database()