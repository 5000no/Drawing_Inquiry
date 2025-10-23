"""
添加图纸对话框
"""
import os
import shutil
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from config import config
from database.db_manager import db_manager


class AddDrawingDialog(QDialog):
    """添加图纸对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_full_path = None  # 新增：类变量存储完整本地路径
        self.setWindowTitle("添加新图纸")
        self.setModal(True)
        self.setFixedSize(500, 280)  # 稍宽以容纳浏览按钮
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("添加新图纸")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        # 产品号输入
        code_layout = QHBoxLayout()
        code_label = QLabel("产品号:")
        code_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("例如: NR1003")
        self.code_input.setFont(QFont("Microsoft YaHei", 10))
        code_layout.addWidget(code_label)
        code_layout.addWidget(self.code_input)
        layout.addLayout(code_layout)
        
        # PDF路径输入 + 浏览按钮
        path_layout = QHBoxLayout()
        path_label = QLabel("PDF路径:")
        path_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("点击'浏览'选择PDF文件")
        self.path_input.setFont(QFont("Microsoft YaHei", 10))
        self.path_input.setReadOnly(True)  # 只读，手动输入禁用
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input, 2)
        
        # 浏览按钮
        browse_btn = QPushButton("浏览")
        browse_btn.setFont(QFont("Microsoft YaHei", 10))
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        browse_btn.clicked.connect(self.browse_pdf)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("添加")
        self.ok_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:pressed { background-color: #1e8449; }
        """)
        self.ok_btn.clicked.connect(self.add_drawing)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFont(QFont("Microsoft YaHei", 10))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def browse_pdf(self):
        """浏览选择PDF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择PDF文件", 
            "",  # 默认目录为空（使用系统默认）
            "PDF Files (*.pdf)"
        )
        if file_path:
            # 提取相对路径（仅文件名）
            relative_path = os.path.basename(file_path)
            self.path_input.setText(relative_path)
            # 新增：用类变量存储完整本地路径（更可靠）
            self.selected_full_path = file_path
            if config.DEBUG:
                print(f"✅ 选择PDF: {relative_path} (完整路径: {file_path})")
    
    def add_drawing(self):
        """添加图纸"""
        product_code = self.code_input.text().strip()
        pdf_path = self.path_input.text().strip()
        
        if not product_code or not pdf_path:
            QMessageBox.warning(self, "错误", "产品号和PDF路径不能为空！请先选择文件。")
            return
        
        if not pdf_path.lower().endswith('.pdf'):
            QMessageBox.warning(self, "错误", "PDF路径必须以 .pdf 结尾！请选择有效的PDF文件。")
            return
        
        # 检查完整本地路径
        if not self.selected_full_path:
            QMessageBox.warning(self, "错误", "请选择有效的PDF文件！（未检测到完整文件路径）")
            if config.DEBUG:
                print("❌ full_path 未设置 - 请点击'浏览'选择文件")
            return
        
        # 构建服务器完整路径
        server_full_path = os.path.join(config.PDF_NETWORK_PATH.rstrip(os.sep), pdf_path)
        
        # 显示复制进度（通过父窗口状态栏，如果可用）
        if self.parent() and hasattr(self.parent(), 'status_bar'):
            self.parent().status_bar.showMessage("正在复制文件到服务器...")
        
        try:
            # 复制文件
            shutil.copy2(self.selected_full_path, server_full_path)
            if config.DEBUG:
                print(f"✅ 文件复制成功: {self.selected_full_path} -> {server_full_path}")
            
            # 复制成功后添加DB
            success = db_manager.add_drawing(product_code, pdf_path)
            if success:
                msg = f"已添加图纸: {product_code}\n文件已复制到服务器: {server_full_path}"
                QMessageBox.information(self, "成功", msg)
                if self.parent() and hasattr(self.parent(), 'status_bar'):
                    self.parent().status_bar.showMessage("复制并添加成功", 3000)
                self.accept()
            else:
                # DB失败，回滚：删除已复制文件
                if os.path.exists(server_full_path):
                    os.remove(server_full_path)
                    if config.DEBUG:
                        print(f"❌ DB失败，已删除复制文件: {server_full_path}")
                QMessageBox.critical(self, "失败", "DB添加失败！产品号可能已存在。\n已删除复制的文件。")
        except Exception as e:
            error_msg = f"文件复制失败: {str(e)}\n请检查网络权限、服务器路径或文件是否被占用。"
            if config.DEBUG:
                print(f"❌ 复制异常: {e}")
            QMessageBox.critical(self, "复制失败", error_msg)
            if self.parent() and hasattr(self.parent(), 'status_bar'):
                self.parent().status_bar.showMessage("复制失败", 3000)