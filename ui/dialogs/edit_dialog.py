"""
编辑图纸对话框
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from config import config
from database.db_manager import db_manager


class EditDrawingDialog(QDialog):
    """编辑图纸对话框"""
    
    def __init__(self, product_code, current_path, parent=None):
        super().__init__(parent)
        self.product_code = product_code
        self.current_path = current_path
        self.setWindowTitle(f"编辑图纸: {product_code}")
        self.setModal(True)
        self.setFixedSize(400, 250)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel(f"编辑图纸: {self.product_code}")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        # 产品号显示（只读）
        code_layout = QHBoxLayout()
        code_label = QLabel("产品号:")
        code_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        code_display = QLabel(self.product_code)
        code_display.setFont(QFont("Microsoft YaHei", 10))
        code_display.setStyleSheet("color: #7f8c8d; padding: 5px;")
        code_layout.addWidget(code_label)
        code_layout.addWidget(code_display)
        layout.addLayout(code_layout)
        
        # PDF路径输入
        path_layout = QHBoxLayout()
        path_label = QLabel("PDF路径:")
        path_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.path_input = QLineEdit(self.current_path)
        self.path_input.setPlaceholderText("修改PDF路径")
        self.path_input.setFont(QFont("Microsoft YaHei", 10))
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        layout.addLayout(path_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("保存")
        self.ok_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }
            QPushButton:hover { background-color: #e67e22; }
            QPushButton:pressed { background-color: #d68910; }
        """)
        self.ok_btn.clicked.connect(self.update_drawing)
        
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
    
    def update_drawing(self):
        """更新图纸"""
        new_pdf_path = self.path_input.text().strip()
        
        if not new_pdf_path:
            QMessageBox.warning(self, "错误", "PDF路径不能为空！")
            return
        
        if not new_pdf_path.lower().endswith('.pdf'):
            QMessageBox.warning(self, "错误", "PDF路径必须以 .pdf 结尾！")
            return
        
        success = db_manager.update_drawing(self.product_code, new_pdf_path)
        if success:
            QMessageBox.information(self, "成功", f"已更新图纸: {self.product_code}")
            self.accept()
        else:
            QMessageBox.critical(self, "失败", "更新失败！")