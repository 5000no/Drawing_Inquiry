"""
数据管理界面组件
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QMessageBox, QLabel, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import os
import shutil  # 新增：用于文件移动

from config import config
from database.db_manager import db_manager
from utils.pdf_handler import pdf_handler
from .dialogs.add_dialog import AddDrawingDialog
from .dialogs.edit_dialog import EditDrawingDialog


class DataManagerWidget(QWidget):
    """数据管理小部件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent  # 引用父窗口，用于状态栏
        self.init_ui()
        self.load_data()  # 初始加载数据
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("图纸数据管理")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        # 表格
        self.table = QTableWidget()
        self.table.setFont(QFont("Microsoft YaHei", 10))
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #ecf0f1;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "产品号", "PDF路径"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # 只读
        layout.addWidget(self.table)
        
        # 按钮栏
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("添加")
        self.add_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:pressed { background-color: #1e8449; }
        """)
        self.add_btn.clicked.connect(self.add_drawing)
        
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover { background-color: #e67e22; }
            QPushButton:pressed { background-color: #d68910; }
        """)
        self.edit_btn.clicked.connect(self.edit_drawing)
        self.edit_btn.setEnabled(False)  # 初始禁用
        
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:pressed { background-color: #a93226; }
        """)
        self.delete_btn.clicked.connect(self.delete_drawing)
        self.delete_btn.setEnabled(False)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        self.refresh_btn.clicked.connect(self.load_data)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # 连接选中事件
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        # 连接双击事件
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
    
    def load_data(self):
        """加载数据到表格"""
        drawings = db_manager.get_all_drawings()
        self.table.setRowCount(len(drawings))
        
        for row, drawing in enumerate(drawings):
            # ID
            id_item = QTableWidgetItem(str(drawing['id']))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, id_item)
            
            # 产品号
            code_item = QTableWidgetItem(drawing['product_code'])
            code_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, code_item)
            
            # PDF路径
            path_item = QTableWidgetItem(drawing['pdf_path'])
            path_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row, 2, path_item)
        
        # 调整列宽
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        
        if config.DEBUG:
            print(f"✅ 加载 {len(drawings)} 条数据")
    
    def on_selection_changed(self):
        """选中行变化"""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def on_item_double_clicked(self, item):
        """双击单元格事件"""
        col = item.column()
        if col == 2:  # PDF路径列
            pdf_path = item.text()
            if self.main_window and self.main_window.status_bar:
                self.main_window.status_bar.showMessage("正在打开PDF...")
            success, message = pdf_handler.open_pdf(pdf_path)
            if success:
                if self.main_window and self.main_window.status_bar:
                    self.main_window.status_bar.showMessage(f"已打开: {pdf_path}", 3000)
            else:
                if self.main_window and self.main_window.status_bar:
                    self.main_window.status_bar.showMessage("打开失败", 3000)
                QMessageBox.critical(self, "错误", message)
    
    def add_drawing(self):
        """添加"""
        dialog = AddDrawingDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()  # 刷新表格
    
    def edit_drawing(self):
        """编辑"""
        if not self.table.selectedItems():
            return
        row = self.table.currentRow()
        product_code = self.table.item(row, 1).text()
        current_path = self.table.item(row, 2).text()
        
        dialog = EditDrawingDialog(product_code, current_path, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
    
    def delete_drawing(self):
        """删除"""
        if not self.table.selectedItems():
            return
        row = self.table.currentRow()
        product_code = self.table.item(row, 1).text()
        pdf_path = self.table.item(row, 2).text()
        
        # 构建服务器PDF路径
        server_pdf_path = os.path.join(config.PDF_NETWORK_PATH.rstrip(os.sep), pdf_path)
        
        # 确认对话框，提示移动文件
        reply = QMessageBox.question(self, "确认删除", 
                                     f"确定删除产品号 '{product_code}' 的图纸吗？\n\n"
                                     f"• 数据库记录将被删除\n"
                                     f"• PDF文件 '{pdf_path}' 将移动到 delete 文件夹",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # 显示进度
            if self.main_window and self.main_window.status_bar:
                self.main_window.status_bar.showMessage("正在删除...")
            
            try:
                # 先移动文件
                if os.path.exists(server_pdf_path):
                    # delete文件夹路径：服务器PDF上级 + delete + 相对路径
                    pdf_parent_dir = os.path.dirname(config.PDF_NETWORK_PATH.rstrip(os.sep))
                    delete_dir = os.path.join(pdf_parent_dir, 'delete')
                    os.makedirs(delete_dir, exist_ok=True)  # 创建delete文件夹如果不存在
                    target_delete_path = os.path.join(delete_dir, pdf_path)
                    
                    # 移动文件
                    shutil.move(server_pdf_path, target_delete_path)
                    if config.DEBUG:
                        print(f"✅ 文件移动成功: {server_pdf_path} -> {target_delete_path}")
                else:
                    if config.DEBUG:
                        print(f"⚠️ 文件不存在: {server_pdf_path}")
                
                # 移动成功后删除DB记录
                db_success = db_manager.delete_drawing(product_code)
                if db_success:
                    msg = f"已删除: {product_code}\n文件已移动到 delete 文件夹。"
                    QMessageBox.information(self, "成功", msg)
                    if self.main_window and self.main_window.status_bar:
                        self.main_window.status_bar.showMessage("删除成功", 3000)
                    self.load_data()  # 刷新表格
                else:
                    # DB失败，回滚：移动文件回原位置
                    if os.path.exists(target_delete_path):
                        shutil.move(target_delete_path, server_pdf_path)
                        if config.DEBUG:
                            print(f"❌ DB失败，已回滚文件: {target_delete_path} -> {server_pdf_path}")
                    QMessageBox.critical(self, "失败", "DB删除失败！\n文件已回滚到原位置。")
            except Exception as e:
                error_msg = f"文件移动失败: {str(e)}\n请检查服务器权限。"
                if config.DEBUG:
                    print(f"❌ 删除异常: {e}")
                QMessageBox.critical(self, "移动失败", error_msg)
                if self.main_window and self.main_window.status_bar:
                    self.main_window.status_bar.showMessage("删除失败", 3000)