"""
数据库管理器
负责所有数据库操作：查询、添加、更新、删除
"""
import pymysql
from contextlib import contextmanager
import time
import hashlib
import threading
from config import config
try:
    # Web 场景下从会话读取激活码/租户信息
    from flask import has_request_context, session
except Exception:
    # 桌面/脚本场景下没有Flask上下文
    has_request_context = lambda: False
    session = {}


class DatabaseManager:
    """数据库管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式：确保只有一个数据库管理器实例"""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化数据库连接"""
        if self._initialized:
            return
        
        self.connection_config = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD,
            'database': config.DB_NAME,
            'charset': config.DB_CHARSET,
            'connect_timeout': 10,
            'autocommit': False  # 手动控制事务
        }
        
        self._initialized = True
        # 多租户：线程覆盖（桌面/脚本可用）
        self._tenant_override = threading.local()
        
        # 测试连接
        if config.DEBUG:
            print("📊 数据库管理器初始化...")
            self._test_connection()
    
    def _test_connection(self):
        """测试数据库连接"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            if config.DEBUG:
                print(f"✅ 数据库连接成功: {config.DB_HOST}")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接（上下文管理器）
        使用with语句自动管理连接
        """
        connection = None
        try:
            connection = pymysql.connect(**self.connection_config)
            yield connection
            connection.commit()
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if connection:
                connection.close()

    # ==================== 多租户支持（按激活码独立数据库） ====================
    def _normalize_code(self, code: str) -> str:
        return (code or '').strip().upper().replace('-', '')

    def tenant_db_from_code(self, code: str) -> str:
        """根据激活码生成稳定的租户数据库名"""
        norm = self._normalize_code(code)
        h = hashlib.sha256(norm.encode()).hexdigest()[:8]
        return f"{config.DB_NAME}_t_{h}"

    def set_tenant_override(self, tenant_db: str | None):
        """显式设置当前线程的租户数据库覆盖（用于桌面/脚本）"""
        self._tenant_override.value = tenant_db

    @contextmanager
    def get_tenant_connection(self, activation_code: str | None = None):
        """
        获取租户数据库连接：
        - 优先使用显式传入的激活码
        - 其次使用当前会话中的 session['tenant_db'] 或 session['activation_code']
        - 再次使用线程覆盖（desktop场景）
        - 若均不可用，回退到主库
        - 若连接报 Unknown database，则自动创建租户库后重试
        """
        tenant_db = None
        # 解析激活码和租户库名
        if activation_code:
            tenant_db = self.tenant_db_from_code(activation_code)
        elif getattr(self._tenant_override, 'value', None):
            tenant_db = self._tenant_override.value
        elif has_request_context():
            tenant_db = session.get('tenant_db')
            if not tenant_db and session.get('activation_code'):
                activation_code = session.get('activation_code')
                tenant_db = self.tenant_db_from_code(activation_code)

        conn_cfg = dict(self.connection_config)
        if tenant_db:
            conn_cfg['database'] = tenant_db

        connection = None
        try:
            # 首次尝试连接
            try:
                connection = pymysql.connect(**conn_cfg)
            except pymysql.err.OperationalError as oe:
                # Unknown database
                if getattr(oe, 'args', None) and oe.args and oe.args[0] == 1049 and tenant_db:
                    # 有激活码时自动创建租户库并重试
                    code_to_use = activation_code
                    if not code_to_use and has_request_context():
                        code_to_use = session.get('activation_code')
                    if code_to_use:
                        try:
                            self.ensure_tenant_database(code_to_use)
                            connection = pymysql.connect(**conn_cfg)
                        except Exception:
                            # 创建失败则抛出原错误
                            raise oe
                    else:
                        # 没有激活码无法创建，抛出原错误
                        raise oe
                else:
                    # 其他错误直接抛出
                    raise

            # 正常使用连接
            yield connection
            connection.commit()
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if connection:
                connection.close()

    def ensure_tenant_database(self, activation_code: str):
        """创建并初始化租户数据库（若不存在）"""
        tenant_db = self.tenant_db_from_code(activation_code)
        server_cfg = dict(self.connection_config)
        server_cfg.pop('database', None)
        with pymysql.connect(**server_cfg) as conn:
            cur = conn.cursor()
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{tenant_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cur.execute(f"USE `{tenant_db}`")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS drawings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_code VARCHAR(100) NOT NULL UNIQUE,
                    pdf_path VARCHAR(500) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            cur.close()
            conn.commit()
        return tenant_db
    
    # ==================== 查询操作 ====================
    
    def search_by_code(self, product_code):
        """
        根据产品号精确查询（最常用）
        
        参数:
            product_code: 产品号（如：NR1001）
        
        返回:
            dict: 图纸信息字典，未找到返回None
        """
        start_time = time.time()
        
        try:
            with self.get_tenant_connection() as conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)  # 返回字典格式
                
                sql = """
                    SELECT id, product_code, pdf_path
                    FROM drawings
                    WHERE product_code = %s
                    LIMIT 1
                """
                
                cursor.execute(sql, (product_code,))
                result = cursor.fetchone()
                cursor.close()
                
                # 记录查询时间
                query_time = (time.time() - start_time) * 1000
                if config.DEBUG:
                    print(f"⚡ 查询耗时: {query_time:.2f}ms")
                
                return result
                
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            return None
    
    def search_fuzzy(self, keyword, limit=None):
        """
        模糊查询（支持产品号模糊匹配）
        
        参数:
            keyword: 关键词
            limit: 返回最大条数
        
        返回:
            list: 图纸信息列表
        """
        if limit is None:
            limit = config.MAX_SEARCH_RESULTS
        
        start_time = time.time()
        
        try:
            with self.get_tenant_connection() as conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                sql = """
                    SELECT id, product_code, pdf_path
                    FROM drawings
                    WHERE product_code LIKE %s
                    ORDER BY product_code
                    LIMIT %s
                """
                
                search_pattern = f"%{keyword}%"
                cursor.execute(sql, (search_pattern, limit))
                results = cursor.fetchall()
                cursor.close()
                
                query_time = (time.time() - start_time) * 1000
                if config.DEBUG:
                    print(f"⚡ 模糊查询耗时: {query_time:.2f}ms, 找到 {len(results)} 条")
                
                return results
                
        except Exception as e:
            print(f"❌ 模糊查询失败: {e}")
            return []
    
    # ==================== 添加操作 ====================
    
    def add_drawing(self, product_code, pdf_path):
        """
        添加单个图纸
        
        参数:
            product_code: 产品号
            pdf_path: PDF路径
        
        返回:
            bool: 成功返回True，失败返回False
        """
        try:
            with self.get_tenant_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                    INSERT INTO drawings (product_code, pdf_path)
                    VALUES (%s, %s)
                """
                
                cursor.execute(sql, (product_code, pdf_path))
                cursor.close()
                
                if config.DEBUG:
                    print(f"✅ 添加成功: {product_code}")
                
                return True
                
        except pymysql.IntegrityError:
            print(f"❌ 产品号已存在: {product_code}")
            return False
        except Exception as e:
            print(f"❌ 添加失败: {e}")
            return False
    
    # ==================== 激活码管理 ====================
    
    def add_activation_code(self, code, description=""):
        """
        添加激活码
        
        参数:
            code: 激活码
            description: 描述
            
        返回:
            bool: 成功返回True，失败返回False
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 优先尝试写入并设置激活状态（兼容 is_active / is_activated 两种列名）
                try:
                    sql = """
                        INSERT INTO activation_codes (code, description, is_active)
                        VALUES (%s, %s, TRUE)
                    """
                    cursor.execute(sql, (code, description))
                except Exception as e:
                    # 兼容旧库：使用 is_activated 列
                    if "Unknown column 'is_active'" in str(e):
                        sql = """
                            INSERT INTO activation_codes (code, description, is_activated)
                            VALUES (%s, %s, TRUE)
                        """
                        cursor.execute(sql, (code, description))
                    else:
                        raise
                finally:
                    cursor.close()
                
                if config.DEBUG:
                    print(f"✅ 添加激活码成功: {code}")
                
                return True
                
        except pymysql.IntegrityError:
            print(f"❌ 激活码已存在: {code}")
            return False
        except Exception as e:
            print(f"❌ 添加激活码失败: {e}")
            return False
    
    def check_activation_code(self, code):
        """
        检查激活码是否有效
        
        参数:
            code: 激活码
            
        返回:
            bool: 有效返回True，无效返回False
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 先按新列名 is_active 检查（不依赖 id 列，直接 SELECT 1）
                try:
                    sql = """
                        SELECT 1 FROM activation_codes
                        WHERE code = %s AND is_active = TRUE
                        LIMIT 1
                    """
                    cursor.execute(sql, (code,))
                except Exception as e:
                    # 兼容旧库：按 is_activated 检查
                    if "Unknown column 'is_active'" in str(e):
                        sql = """
                            SELECT 1 FROM activation_codes
                            WHERE code = %s AND is_activated = TRUE
                            LIMIT 1
                        """
                        cursor.execute(sql, (code,))
                    else:
                        raise
                result = cursor.fetchone()
                cursor.close()
                
                # 若仍无结果，作为兜底：只要存在该激活码则视为有效
                if not result:
                    with self.get_connection() as conn2:
                        c2 = conn2.cursor()
                        c2.execute("SELECT 1 FROM activation_codes WHERE code = %s LIMIT 1", (code,))
                        r2 = c2.fetchone()
                        c2.close()
                        return r2 is not None
                
                return True
                
        except Exception as e:
            print(f"❌ 检查激活码失败: {e}")
            return False
    
    def get_all_activation_codes(self):
        """
        获取所有激活码
        
        返回:
            list: 激活码列表
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # 优先尝试使用 is_active 列
                try:
                    sql = """
                        SELECT code, description, created_at, is_active
                        FROM activation_codes
                        ORDER BY created_at DESC
                    """
                    cursor.execute(sql)
                except Exception as e:
                    # 兼容旧库，改用 is_activated 列并命名为 is_active
                    if "Unknown column 'is_active'" in str(e):
                        sql = """
                            SELECT code, description, created_at, is_activated AS is_active
                            FROM activation_codes
                            ORDER BY created_at DESC
                        """
                        cursor.execute(sql)
                    else:
                        raise
                results = cursor.fetchall()
                cursor.close()
                
                return results
                
        except Exception as e:
            print(f"❌ 获取激活码失败: {e}")
            return []
    
    # ==================== 用户管理 ====================
    
    def register_user(self, username, password, email, activation_code):
        """
        注册用户
        
        参数:
            username: 用户名
            password: 密码
            email: 邮箱
            activation_code: 激活码
            
        返回:
            bool: 成功返回True，失败返回False
        """
        # 检查激活码是否有效
        if not self.check_activation_code(activation_code):
            print(f"❌ 激活码无效: {activation_code}")
            return False
        
        # 密码哈希
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            # 确保对应租户库存在
            tenant_db = self.ensure_tenant_database(activation_code)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # 尝试写入租户库名（如旧库无该列则动态添加）
                try:
                    cursor.execute("SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME='users' AND COLUMN_NAME='tenant_db'", (self.connection_config['database'],))
                    has_col = cursor.fetchone() is not None
                    if not has_col:
                        cursor.execute("ALTER TABLE users ADD COLUMN tenant_db VARCHAR(64) NULL COMMENT '租户数据库名'")
                except Exception:
                    pass

                try:
                    sql = """
                        INSERT INTO users (username, password_hash, email, activation_code, tenant_db)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (username, password_hash, email, activation_code, tenant_db))
                except Exception:
                    sql2 = """
                        INSERT INTO users (username, password_hash, email, activation_code)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(sql2, (username, password_hash, email, activation_code))
                cursor.close()
                
                if config.DEBUG:
                    print(f"✅ 用户注册成功: {username}")
                
                return True
                
        except pymysql.IntegrityError:
            print(f"❌ 用户名已存在: {username}")
            return False
        except Exception as e:
            print(f"❌ 用户注册失败: {e}")
            return False

    def username_exists(self, username):
        """
        检查用户名是否已存在
        
        参数:
            username: 用户名
        
        返回:
            bool: 已存在返回True，不存在返回False
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM users WHERE username = %s LIMIT 1", (username,))
                exists = cursor.fetchone() is not None
                cursor.close()
                return exists
        except Exception as e:
            print(f"❌ 检查用户名失败: {e}")
            return False
    
    def login_user(self, username, password):
        """
        用户登录
        
        参数:
            username: 用户名
            password: 密码
            
        返回:
            dict: 用户信息，登录失败返回None
        """
        # 密码哈希
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                # 查询用户
                sql = """
                    SELECT id, username, email, activation_code, tenant_db, created_at, last_login, is_active
                    FROM users
                    WHERE username = %s AND password_hash = %s AND is_active = TRUE
                    LIMIT 1
                """
                try:
                    cursor.execute(sql, (username, password_hash))
                except Exception:
                    # 兼容旧库无tenant_db列
                    sql_fallback = """
                        SELECT id, username, email, activation_code, created_at, last_login, is_active
                        FROM users
                        WHERE username = %s AND password_hash = %s AND is_active = TRUE
                        LIMIT 1
                    """
                    cursor.execute(sql_fallback, (username, password_hash))
                user = cursor.fetchone()
                
                # 更新最后登录时间
                if user:
                    update_sql = """
                        UPDATE users
                        SET last_login = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """
                    cursor.execute(update_sql, (user['id'],))
                
                cursor.close()
                # 附加租户库名（旧库兼容）
                if user and (user.get('tenant_db') is None):
                    user['tenant_db'] = self.tenant_db_from_code(user.get('activation_code'))
                return user
                
        except Exception as e:
            print(f"❌ 用户登录失败: {e}")
            return None
    
    def get_user_activation_code(self, username):
        """
        获取用户的激活码
        
        参数:
            username: 用户名
            
        返回:
            str: 激活码，未找到返回None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                    SELECT activation_code
                    FROM users
                    WHERE username = %s AND is_active = TRUE
                    LIMIT 1
                """
                
                cursor.execute(sql, (username,))
                result = cursor.fetchone()
                cursor.close()
                
                return result[0] if result else None
                
        except Exception as e:
            print(f"❌ 获取用户激活码失败: {e}")
            return None
    
    def batch_add_drawings(self, drawings_list):
        """
        批量添加图纸
        
        参数:
            drawings_list: [(product_code, pdf_path), ...]
        
        返回:
            tuple: (成功数量, 失败数量)
        """
        success_count = 0
        fail_count = 0
        
        try:
            with self.get_tenant_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                    INSERT INTO drawings (product_code, pdf_path)
                    VALUES (%s, %s)
                """
                
                for product_code, pdf_path in drawings_list:
                    try:
                        cursor.execute(sql, (product_code, pdf_path))
                        success_count += 1
                    except pymysql.IntegrityError:
                        fail_count += 1
                        if config.DEBUG:
                            print(f"⚠️ 跳过重复: {product_code}")
                
                cursor.close()
                
                if config.DEBUG:
                    print(f"✅ 批量添加完成: 成功 {success_count}, 失败 {fail_count}")
                
                return (success_count, fail_count)
                
        except Exception as e:
            print(f"❌ 批量添加失败: {e}")
            return (success_count, fail_count)
    
    # ==================== 更新操作 ====================
    
    def update_drawing(self, product_code, new_pdf_path):
        """
        更新图纸路径
        
        参数:
            product_code: 产品号
            new_pdf_path: 新的PDF路径
        
        返回:
            bool: 成功返回True
        """
        try:
            with self.get_tenant_connection() as conn:
                cursor = conn.cursor()
                
                sql = """
                    UPDATE drawings
                    SET pdf_path = %s
                    WHERE product_code = %s
                """
                
                cursor.execute(sql, (new_pdf_path, product_code))
                affected_rows = cursor.rowcount
                cursor.close()
                
                if affected_rows > 0:
                    if config.DEBUG:
                        print(f"✅ 更新成功: {product_code}")
                    return True
                else:
                    print(f"⚠️ 产品号不存在: {product_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            return False
    
    # ==================== 删除操作 ====================
    
    def delete_drawing(self, product_code):
        """
        删除图纸
        
        参数:
            product_code: 产品号
        
        返回:
            bool: 成功返回True
        """
        try:
            with self.get_tenant_connection() as conn:
                cursor = conn.cursor()
                
                sql = "DELETE FROM drawings WHERE product_code = %s"
                
                cursor.execute(sql, (product_code,))
                affected_rows = cursor.rowcount
                cursor.close()
                
                if affected_rows > 0:
                    if config.DEBUG:
                        print(f"✅ 删除成功: {product_code}")
                    return True
                else:
                    print(f"⚠️ 产品号不存在: {product_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ 删除失败: {e}")
            return False
    
    # ==================== 统计操作 ====================
    
    def get_total_count(self):
        """
        获取图纸总数
        
        返回:
            int: 图纸总数
        """
        try:
            with self.get_tenant_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM drawings")
                count = cursor.fetchone()[0]
                cursor.close()
                return count
        except Exception as e:
            print(f"❌ 统计失败: {e}")
            return 0
            
    def init_database(self):
        """初始化数据库（创建表）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 创建激活码表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS activation_codes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        code VARCHAR(50) NOT NULL UNIQUE,
                        description VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # 创建用户表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(50) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        email VARCHAR(100),
                        activation_code VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        FOREIGN KEY (activation_code) REFERENCES activation_codes(code) ON DELETE RESTRICT
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # 创建图纸表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS drawings (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product_code VARCHAR(50) NOT NULL UNIQUE,
                        pdf_path VARCHAR(255) NOT NULL,
                        activation_code VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (activation_code) REFERENCES activation_codes(code) ON DELETE RESTRICT
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                cursor.close()
                
                if config.DEBUG:
                    print("✅ 数据库初始化成功")
                
                return True
                
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            return False
    
    def get_all_drawings(self, limit=1000):
        """
        获取所有图纸（用于数据管理）
        
        参数:
            limit: 最大返回数量
        
        返回:
            list: 图纸列表
        """
        try:
            with self.get_tenant_connection() as conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                sql = """
                    SELECT id, product_code, pdf_path
                    FROM drawings
                    ORDER BY id
                    LIMIT %s
                """
                
                cursor.execute(sql, (limit,))
                results = cursor.fetchall()
                cursor.close()
                
                return results
                
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            return []


# 创建全局单例实例
db_manager = DatabaseManager()