"""
图纸查询系统 - Web版本
Flask Web应用主文件
"""
from flask import Flask, render_template, request, jsonify, send_file, abort, redirect, url_for, session
from flask_cors import CORS
import os
import json
import re
import time
import hmac
import hashlib
import base64
from functools import wraps
from config import config
from database.db_manager import db_manager
from utils.pdf_handler import pdf_handler

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 简单的登录校验装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 移动端令牌工具
def _sign_token(payload: dict) -> str:
    """生成简易HMAC令牌（包含激活码与过期时间）"""
    data = json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode()
    sig = hmac.new(config.SECRET_KEY.encode(), data, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(data).decode().rstrip('=') + '.' + base64.urlsafe_b64encode(sig).decode().rstrip('=')

def _verify_token(token: str):
    """校验令牌并返回载荷，失败返回None"""
    try:
        if not token:
            return None
        parts = token.split('.')
        if len(parts) != 2:
            return None
        d, s = parts
        # 补齐base64填充
        pad = lambda x: x + '==' if len(x) % 4 else x
        data = base64.urlsafe_b64decode(pad(d))
        sig = base64.urlsafe_b64decode(pad(s))
        expected = hmac.new(config.SECRET_KEY.encode(), data, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(data.decode())
        exp = payload.get('exp')
        if exp and time.time() > float(exp):
            return None
        return payload
    except Exception:
        return None

# 统一API登录校验（统计接口除外）
@app.before_request
def require_login_for_api():
    path = request.path
    # 放行登录/注册、静态资源、统计接口
    allow_paths = {
        '/login', '/register', '/logout', '/api/auth/login', '/api/auth/register', '/api/statistics'
    }
    if path.startswith('/static/'):
        return
    # 移动端接口使用令牌鉴权，统一放行到具体路由处理
    if path.startswith('/api/mobile/'):
        return
    if path in allow_paths:
        return
    # 对所有 /api/* 接口进行登录校验
    if path.startswith('/api/') and not session.get('user_id'):
        return jsonify({'success': False, 'message': '未登录，请先登录'}), 401

@app.route('/')
def index():
    """主页 - 自动检测设备类型"""
    # 未登录跳转到登录页
    if not session.get('user_id'):
        return redirect(url_for('login'))
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # 检测移动设备
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone']
    is_mobile = any(keyword in user_agent for keyword in mobile_keywords)
    
    # 根据设备类型选择模板
    template = 'index_mobile_optimized.html' if is_mobile else 'index.html'
    
    return render_template(template, 
                         app_name=config.APP_NAME, 
                         version=config.VERSION)

@app.route('/mobile')
def mobile_index():
    """移动端专用页面"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('index_mobile_optimized.html', 
                         app_name=config.APP_NAME, 
                         version=config.VERSION)

@app.route('/desktop')
def desktop_index():
    """桌面端专用页面"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('index.html', 
                         app_name=config.APP_NAME, 
                         version=config.VERSION)

# ==================== 移动端 API（小程序） ====================
@app.route('/api/mobile/register', methods=['POST'])
def mobile_register():
    """移动端注册，返回令牌"""
    try:
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()
        email = (data.get('email') or '').strip()
        activation_code = (data.get('activation_code') or '').strip()
        if not username or not password or not activation_code:
            return jsonify({'success': False, 'message': '用户名、密码、激活码必填'}), 400
        if db_manager.username_exists(username):
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        ok = db_manager.register_user(username, password, email, activation_code)
        if not ok:
            return jsonify({'success': False, 'message': '注册失败'}), 400
        user = db_manager.login_user(username, password)
        if not user:
            return jsonify({'success': False, 'message': '注册后登录失败'}), 500
        tenant = user.get('tenant_db') or db_manager.tenant_db_from_code(user['activation_code'])
        payload = {
            'uid': user['id'],
            'username': user['username'],
            'code': user['activation_code'],
            'tenant': tenant,
            'exp': int(time.time() + 7 * 24 * 3600)
        }
        token = _sign_token(payload)
        return jsonify({'success': True, 'token': token, 'user': {'id': user['id'], 'username': user['username'], 'activation_code': user['activation_code']}})
    except Exception as e:
        return jsonify({'success': False, 'message': f'移动端注册失败: {str(e)}'}), 500

@app.route('/api/mobile/login', methods=['POST'])
def mobile_login():
    """移动端登录，返回令牌"""
    try:
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()
        if not username or not password:
            return jsonify({'success': False, 'message': '请输入用户名和密码'}), 400
        user = db_manager.login_user(username, password)
        if not user:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        tenant = user.get('tenant_db') or db_manager.tenant_db_from_code(user['activation_code'])
        payload = {
            'uid': user['id'],
            'username': user['username'],
            'code': user['activation_code'],
            'tenant': tenant,
            'exp': int(time.time() + 7 * 24 * 3600)
        }
        token = _sign_token(payload)
        return jsonify({'success': True, 'token': token, 'user': {'id': user['id'], 'username': user['username'], 'activation_code': user['activation_code']}})
    except Exception as e:
        return jsonify({'success': False, 'message': f'移动端登录失败: {str(e)}'}), 500

@app.route('/api/mobile/upload', methods=['POST'])
def mobile_upload():
    """移动端上传PDF（支持微信小程序的wx.uploadFile）"""
    try:
        # 令牌可以从Header Authorization: Bearer xxx 或表单字段 token 获取
        auth_header = request.headers.get('Authorization', '')
        token = ''
        if auth_header.lower().startswith('bearer '):
            token = auth_header.split(' ', 1)[1].strip()
        token = token or request.form.get('token', '')
        payload = _verify_token(token)
        if not payload:
            return jsonify({'success': False, 'message': '未授权或令牌无效'}), 401
        activation_code = payload.get('code')

        product_code = (request.form.get('product_code') or '').strip()
        pdf_file = request.files.get('file') or request.files.get('pdf_file')
        if not product_code or not pdf_file:
            return jsonify({'success': False, 'message': '产品号和PDF文件不能为空'}), 400
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'message': '只能上传PDF文件'}), 400

        # 生成文件名
        import uuid
        file_extension = '.pdf'
        filename = f"{product_code}_{uuid.uuid4().hex[:8]}{file_extension}"

        # 保存文件到服务器（按激活码分目录）
        full_path = pdf_handler.get_full_path(filename, activation_code=activation_code)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        pdf_file.save(full_path)

        # 在租户库中判断是否重复并插入
        with db_manager.get_tenant_connection(activation_code=activation_code) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM drawings WHERE product_code = %s", (product_code,))
            exists = cursor.fetchone()
            if exists:
                cursor.close()
                return jsonify({'success': False, 'message': f'产品号 "{product_code}" 已存在'}), 400
            cursor.execute(
                "INSERT INTO drawings (product_code, pdf_path) VALUES (%s, %s)",
                (product_code, filename)
            )
            new_id = cursor.lastrowid
            cursor.close()

        # 返回可用于预览的URL（移动端专用，带令牌）
        pdf_url = url_for('mobile_serve_pdf', drawing_id=new_id, _external=True) + f"?token={token}"
        return jsonify({'success': True, 'data': {'id': new_id, 'product_code': product_code, 'pdf_path': filename, 'pdf_url': pdf_url}})
    except Exception as e:
        return jsonify({'success': False, 'message': f'上传失败: {str(e)}'}), 500

@app.route('/api/mobile/pdf/<int:drawing_id>')
def mobile_serve_pdf(drawing_id):
    """移动端提供PDF文件服务（使用令牌确定租户库与文件路径）"""
    try:
        token = request.args.get('token', '')
        payload = _verify_token(token)
        if not payload:
            abort(401, '未授权或令牌无效')
        activation_code = payload.get('code')

        # 根据ID查询图纸信息（在对应租户库）
        with db_manager.get_tenant_connection(activation_code=activation_code) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pdf_path FROM drawings WHERE id = %s", (drawing_id,))
            result = cursor.fetchone()
            cursor.close()
        if not result:
            abort(404, '图纸不存在')

        pdf_path = result[0]
        full_path = pdf_handler.get_full_path(pdf_path, activation_code=activation_code)
        if not os.path.exists(full_path):
            abort(404, 'PDF文件不存在')
        return send_file(full_path, mimetype='application/pdf', as_attachment=False, download_name=pdf_path)
    except Exception as e:
        abort(500, f"服务器错误: {str(e)}")

@app.route('/api/search', methods=['POST'])
def search_drawing():
    """搜索图纸API - 优化响应速度"""
    try:
        data = request.get_json()
        product_code = data.get('product_code', '').strip()
        
        if not product_code:
            return jsonify({
                'success': False,
                'message': '请输入产品号'
            })
        
        # 使用现有的数据库管理器查询
        drawing = db_manager.search_by_code(product_code)
        
        if drawing:
            # 异步检查PDF文件（提高响应速度）
            pdf_exists = True  # 先假设存在，避免网络延迟
            pdf_path = drawing['pdf_path']
            
            # 简单检查文件路径格式
            try:
                full_path = pdf_handler.get_full_path(pdf_path)
                import os
                pdf_exists = os.path.exists(full_path)
            except:
                pdf_exists = False
            
            return jsonify({
                'success': True,
                'data': {
                    'id': drawing['id'],
                    'product_code': drawing['product_code'],
                    'pdf_path': drawing['pdf_path'],
                    'pdf_exists': pdf_exists,
                    'pdf_url': f'/api/pdf/{drawing["id"]}' if pdf_exists else None
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'未找到产品号为 "{product_code}" 的图纸'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询出错: {str(e)}'
        })

@app.route('/api/search/fuzzy', methods=['POST'])
def search_fuzzy():
    """模糊搜索API"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        limit = data.get('limit', 20)
        
        if not keyword:
            return jsonify({
                'success': False,
                'message': '请输入搜索关键词'
            })
        
        # 使用现有的模糊搜索功能
        results = db_manager.search_fuzzy(keyword, limit)
        
        # 为每个结果添加PDF URL
        for result in results:
            pdf_exists, _ = pdf_handler.check_exists(result['pdf_path'])
            result['pdf_exists'] = pdf_exists
            result['pdf_url'] = f'/api/pdf/{result["id"]}' if pdf_exists else None
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'搜索出错: {str(e)}'
        })

@app.route('/api/pdf/<int:drawing_id>')
def serve_pdf(drawing_id):
    """提供PDF文件服务"""
    try:
        # 根据ID查询图纸信息
        with db_manager.get_tenant_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pdf_path FROM drawings WHERE id = %s", (drawing_id,))
            result = cursor.fetchone()
            cursor.close()
        
        if not result:
            abort(404, "图纸不存在")
        
        pdf_path = result[0]
        full_path = pdf_handler.get_full_path(pdf_path)
        
        if not os.path.exists(full_path):
            abort(404, "PDF文件不存在")
        
        return send_file(full_path, 
                        mimetype='application/pdf',
                        as_attachment=False,
                        download_name=pdf_path)
        
    except Exception as e:
        abort(500, f"服务器错误: {str(e)}")

@app.route('/api/statistics')
def get_statistics():
    """获取统计信息API - 实时更新"""
    try:
        from flask import make_response
        
        total_count = db_manager.get_total_count()
        response_data = {
            'success': True,
            'data': {
                'total_drawings': total_count,
                'app_name': config.APP_NAME,
                'version': config.VERSION,
                'environment': config.ENVIRONMENT
            }
        }
        
        # 不使用缓存，确保数据实时更新
        response = make_response(jsonify(response_data))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计信息失败: {str(e)}'
        })

@app.route('/admin')
@login_required
def admin_panel():
    """管理员面板页面"""
    return render_template('admin_panel.html', 
                         app_name=config.APP_NAME, 
                         version=config.VERSION)

# 登录页面与逻辑
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', app_name=config.APP_NAME, version=config.VERSION)
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            return render_template('login.html', app_name=config.APP_NAME, version=config.VERSION, error='请输入用户名和密码')
        user = db_manager.login_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['activation_code'] = user['activation_code']
            session['tenant_db'] = user.get('tenant_db') or db_manager.tenant_db_from_code(user['activation_code'])
            return redirect(url_for('index'))
        else:
            return render_template('login.html', app_name=config.APP_NAME, version=config.VERSION, error='用户名或密码错误')
    except Exception as e:
        return render_template('login.html', app_name=config.APP_NAME, version=config.VERSION, error=f'登录失败: {str(e)}')

# 注册页面与逻辑（通过激活码注册，允许同码多用户）
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html', app_name=config.APP_NAME, version=config.VERSION)
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm', '').strip()
        email = request.form.get('email', '').strip()
        raw_code = request.form.get('activation_code', '').strip()
        activation_code = re.sub(r"\s+", "", raw_code).upper()
        if not username or not password or not activation_code:
            return render_template('register.html', app_name=config.APP_NAME, version=config.VERSION, error='请填写用户名、密码和激活码')
        if password != confirm:
            return render_template('register.html', app_name=config.APP_NAME, version=config.VERSION, error='两次输入的密码不一致')
        # 激活码格式校验（要求 VB-XXXXXXXXXXXX-XXXX 全大写）
        if not re.match(r'^VB-[A-Z0-9]{12}-[A-Z0-9]{4}$', activation_code):
            return render_template('register.html', app_name=config.APP_NAME, version=config.VERSION, error='激活码格式不正确，请输入 VB-XXXXXXXXXXXX-XXXX（需大写）')
        # 激活码有效性校验
        if not db_manager.check_activation_code(activation_code):
            return render_template('register.html', app_name=config.APP_NAME, version=config.VERSION, error='激活码无效或未激活')
        # 用户名重复校验
        if db_manager.username_exists(username):
            return render_template('register.html', app_name=config.APP_NAME, version=config.VERSION, error='用户名已存在，请换一个')
        ok = db_manager.register_user(username, password, email, activation_code)
        if ok:
            # 注册成功后自动登录
            user = db_manager.login_user(username, password)
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['activation_code'] = user['activation_code']
                session['tenant_db'] = user.get('tenant_db') or db_manager.tenant_db_from_code(user['activation_code'])
                return redirect(url_for('index'))
            return redirect(url_for('login'))
        else:
            return render_template('register.html', app_name=config.APP_NAME, version=config.VERSION, error='注册失败，请稍后再试')
    except Exception as e:
        return render_template('register.html', app_name=config.APP_NAME, version=config.VERSION, error=f'注册失败: {str(e)}')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/admin/drawings', methods=['GET'])
def get_all_drawings():
    """获取所有图纸数据API"""
    try:
        drawings = db_manager.get_all_drawings(limit=1000)
        return jsonify({
            'success': True,
            'data': drawings,
            'count': len(drawings)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取数据失败: {str(e)}'
        })

@app.route('/api/admin/drawings', methods=['POST'])
def add_drawing():
    """添加图纸API"""
    try:
        data = request.get_json()
        product_code = data.get('product_code', '').strip()
        pdf_path = data.get('pdf_path', '').strip()
        
        if not product_code or not pdf_path:
            return jsonify({
                'success': False,
                'message': '产品号和PDF路径不能为空'
            })
        
        # 检查产品号是否已存在
        existing = db_manager.search_by_code(product_code)
        if existing:
            return jsonify({
                'success': False,
                'message': f'产品号 "{product_code}" 已存在'
            })
        
        # 添加到数据库
        success = db_manager.add_drawing(product_code, pdf_path)
        
        if success:
            return jsonify({
                'success': True,
                'message': '添加成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '添加失败'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加失败: {str(e)}'
        })

@app.route('/api/admin/drawings/<int:drawing_id>', methods=['PUT'])
def update_drawing(drawing_id):
    """更新图纸API"""
    try:
        data = request.get_json()
        product_code = data.get('product_code', '').strip()
        pdf_path = data.get('pdf_path', '').strip()
        
        if not product_code:
            return jsonify({
                'success': False,
                'message': '产品号不能为空'
            })
        
        if not pdf_path:
            return jsonify({
                'success': False,
                'message': 'PDF路径不能为空'
            })
        
        # 先获取原有记录
        with db_manager.get_tenant_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT product_code FROM drawings WHERE id = %s", (drawing_id,))
            result = cursor.fetchone()
            cursor.close()
        
        if not result:
            return jsonify({
                'success': False,
                'message': '图纸不存在'
            })
        
        old_product_code = result[0]
        
        # 如果产品号发生变化，检查新产品号是否已存在
        if product_code != old_product_code:
            existing = db_manager.search_by_code(product_code)
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'产品号 "{product_code}" 已存在'
                })
        
        # 更新数据库
        with db_manager.get_tenant_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE drawings SET product_code = %s, pdf_path = %s WHERE id = %s",
                (product_code, pdf_path, drawing_id)
            )
            conn.commit()
            cursor.close()
        
        return jsonify({
            'success': True,
            'message': '更新成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        })

@app.route('/api/admin/drawings/upload', methods=['POST'])
def upload_drawing():
    """上传图纸文件API"""
    try:
        product_code = request.form.get('product_code', '').strip()
        pdf_file = request.files.get('pdf_file')
        
        if not product_code or not pdf_file:
            return jsonify({
                'success': False,
                'message': '产品号和PDF文件不能为空'
            })
        
        # 检查产品号是否已存在
        existing = db_manager.search_by_code(product_code)
        if existing:
            return jsonify({
                'success': False,
                'message': f'产品号 "{product_code}" 已存在'
            })
        
        # 验证文件类型
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({
                'success': False,
                'message': '只能上传PDF文件'
            })
        
        # 生成文件名
        import os
        import uuid
        file_extension = '.pdf'
        filename = f"{product_code}_{uuid.uuid4().hex[:8]}{file_extension}"
        
        # 保存文件到服务器
        upload_dir = os.path.join(config.PDF_NETWORK_PATH.rstrip(os.sep))
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        pdf_file.save(file_path)
        
        # 添加到数据库
        success = db_manager.add_drawing(product_code, filename)
        
        if success:
            return jsonify({
                'success': True,
                'message': '上传成功',
                'filename': filename
            })
        else:
            # 如果数据库添加失败，删除已上传的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({
                'success': False,
                'message': '数据库添加失败'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'上传失败: {str(e)}'
        })

@app.route('/api/admin/drawings/<int:drawing_id>/upload', methods=['PUT'])
def update_drawing_file(drawing_id):
    """更新图纸文件API"""
    try:
        product_code = request.form.get('product_code', '').strip()
        pdf_file = request.files.get('pdf_file')
        
        if not product_code:
            return jsonify({
                'success': False,
                'message': '产品号不能为空'
            })
        
        if not pdf_file:
            return jsonify({
                'success': False,
                'message': 'PDF文件不能为空'
            })
        
        # 验证文件类型
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({
                'success': False,
                'message': '只能上传PDF文件'
            })
        
        # 获取原有记录
        with db_manager.get_tenant_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT product_code, pdf_path FROM drawings WHERE id = %s", (drawing_id,))
            result = cursor.fetchone()
            cursor.close()
        
        if not result:
            return jsonify({
                'success': False,
                'message': '图纸不存在'
            })
        
        old_product_code, old_pdf_path = result
        
        # 如果产品号发生变化，检查新产品号是否已存在
        if product_code != old_product_code:
            existing = db_manager.search_by_code(product_code)
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'产品号 "{product_code}" 已存在'
                })
        
        # 生成新文件名
        import os
        import uuid
        file_extension = '.pdf'
        filename = f"{product_code}_{uuid.uuid4().hex[:8]}{file_extension}"
        
        # 保存新文件
        upload_dir = os.path.join(config.PDF_NETWORK_PATH.rstrip(os.sep))
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        pdf_file.save(file_path)
        
        # 更新数据库
        with db_manager.get_tenant_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE drawings SET product_code = %s, pdf_path = %s WHERE id = %s",
                (product_code, filename, drawing_id)
            )
            conn.commit()
            cursor.close()
        
        # 删除旧文件
        old_file_path = os.path.join(upload_dir, old_pdf_path)
        if os.path.exists(old_file_path):
            try:
                os.remove(old_file_path)
            except:
                pass  # 忽略删除旧文件的错误
        
        return jsonify({
            'success': True,
            'message': '更新成功',
            'filename': filename
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        })

@app.route('/api/admin/drawings/batch', methods=['DELETE'])
def delete_drawings_batch():
    """批量删除图纸API"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({
                'success': False,
                'message': '请选择要删除的图纸'
            })
        
        deleted_count = 0
        
        for drawing_id in ids:
            try:
                # 获取产品号
                with db_manager.get_tenant_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT product_code FROM drawings WHERE id = %s", (drawing_id,))
                    result = cursor.fetchone()
                    cursor.close()
                
                if result:
                    product_code = result[0]
                    success = db_manager.delete_drawing(product_code)
                    if success:
                        deleted_count += 1
                        
            except Exception as e:
                print(f"删除图纸 {drawing_id} 失败: {e}")
                continue
        
        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 个图纸',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        })

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'message': '页面不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500

def find_available_port(start_port=5000, max_attempts=10):
    """查找可用端口"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

def get_local_ip():
    """获取本机IP地址"""
    import socket
    try:
        # 连接到一个不存在的地址来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def check_and_open_firewall_port(port):
    """检查并尝试开放防火墙端口"""
    import subprocess
    import os
    
    try:
        # 检查是否以管理员身份运行
        is_admin = os.getenv('USERNAME') == 'Administrator' or \
                  subprocess.run(['net', 'session'], capture_output=True, text=True).returncode == 0
        
        if is_admin:
            # 尝试添加防火墙规则
            cmd = f'netsh advfirewall firewall add rule name="Flask Web App Port {port}" dir=in action=allow protocol=TCP localport={port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ 已自动开放防火墙端口 {port}")
                return True
            else:
                print(f"⚠️  防火墙端口开放失败: {result.stderr}")
        else:
            print(f"⚠️  需要管理员权限开放端口 {port}")
            print(f"💡 手动开放命令: netsh advfirewall firewall add rule name=\"Flask Web App Port {port}\" dir=in action=allow protocol=TCP localport={port}")
    except Exception as e:
        print(f"⚠️  防火墙配置检查失败: {e}")
    
    return False

if __name__ == '__main__':
    # 查找可用端口
    port = find_available_port(5000, 20)
    if not port:
        print("❌ 无法找到可用端口，请检查网络配置")
        exit(1)
    
    # 获取本机IP
    local_ip = get_local_ip()
    
    # 尝试自动配置防火墙
    check_and_open_firewall_port(port)
    
    # 开发模式运行
    print(f"🚀 启动 {config.APP_NAME} Web版本 v{config.VERSION}")
    print(f"🌐 本地访问: http://localhost:{port}")
    print(f"🌐 局域网访问: http://{local_ip}:{port}")
    print(f"📊 数据库: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
    print(f"🔧 使用端口: {port}")
    
    if port != 5000:
        print(f"⚠️  注意: 5000端口被占用，已自动切换到端口 {port}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=config.DEBUG,
        threaded=True
    )