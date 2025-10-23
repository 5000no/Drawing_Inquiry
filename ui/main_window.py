"""
主窗口界面
图纸查询系统的主界面
"""
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLineEdit, QPushButton, QTextEdit, QLabel, QMessageBox, QGroupBox, 
    QStatusBar
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from config import config
from database.db_manager import db_manager
from utils.pdf_handler import pdf_handler
from ui.data_manager import DataManagerWidget
from ui.pdf_viewer import PDFViewer


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 当前查询到的图纸信息
        self.current_drawing = None
        
        # 初始化界面
        self.init_ui()
        
        # 显示欢迎信息
        self.show_welcome()
    
    def init_ui(self):
        """初始化界面"""
        
        # 设置窗口属性
        self.setWindowTitle(f"{config.APP_NAME} v{config.VERSION}")
        self.setGeometry(100, 100, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Tab 控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                color: #2c3e50;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
        """)
        main_layout.addWidget(self.tab_widget)
        
        # ========== Tab 1: 快速查询 ==========
        query_tab = QWidget()
        query_layout = QHBoxLayout()  # 水平布局：左侧信息 + 右侧PDF
        query_tab.setLayout(query_layout)
        
        # 左侧面板：标题 + 搜索 + 信息显示
        left_panel = QWidget()
        left_panel.setFixedWidth(400)  # 固定左侧宽度，适配21寸
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # 标题
        title_label = QLabel(config.APP_NAME)
        title_label.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; padding: 20px;")
        left_layout.addWidget(title_label)
        
        # 搜索区域
        search_group = QGroupBox("快速查询")
        search_group.setFont(QFont("Microsoft YaHei", 11))
        search_layout = QHBoxLayout()
        
        label = QLabel("产品号:")
        label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        search_layout.addWidget(label)
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("请输入产品号，按回车查询...")
        self.code_input.setFont(QFont("Microsoft YaHei", 14))
        self.code_input.setMinimumHeight(40)
        self.code_input.returnPressed.connect(self.search_drawing)
        search_layout.addWidget(self.code_input, 3)
        
        self.search_btn = QPushButton("查询")
        self.search_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.search_btn.setMinimumHeight(40)
        self.search_btn.setMinimumWidth(100)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #21618c; }
        """)
        self.search_btn.clicked.connect(self.search_drawing)
        search_layout.addWidget(self.search_btn)
        
        search_group.setLayout(search_layout)
        left_layout.addWidget(search_group)
        
        # 信息显示
        self.info_display = QTextEdit()
        self.info_display.setFont(QFont("Microsoft YaHei", 10))
        self.info_display.setReadOnly(True)
        self.info_display.setStyleSheet("background-color: #f8f9fa; border: 1px solid #bdc3c7; border-radius: 5px; padding: 10px;")
        self.info_display.setMinimumHeight(400)
        left_layout.addWidget(self.info_display)
        
        # 操作按钮
        op_layout = QHBoxLayout()
        stats_btn = QPushButton("统计")
        stats_btn.setFont(QFont("Microsoft YaHei", 10))
        stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        stats_btn.clicked.connect(self.show_statistics)
        
        clear_btn = QPushButton("清空")
        clear_btn.setFont(QFont("Microsoft YaHei", 10))
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        clear_btn.clicked.connect(self.clear_display)
        
        op_layout.addStretch()
        op_layout.addWidget(stats_btn)
        op_layout.addWidget(clear_btn)
        op_layout.addStretch()
        left_layout.addLayout(op_layout)
        
        left_layout.addStretch()
        query_layout.addWidget(left_panel)
        
        # 右侧大区域：PDF查看器
        self.pdf_viewer = PDFViewer()
        query_layout.addWidget(self.pdf_viewer, 1)  # 自适应宽度，占大部分
        
        self.tab_widget.addTab(query_tab, "快速查询")
        
        # ========== Tab 2: 数据管理 ==========
        self.data_manager = DataManagerWidget()
        self.tab_widget.addTab(self.data_manager, "数据管理")
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
    
    def show_welcome(self):
        """显示欢迎信息"""
        welcome_text = f"""
╔═══════════════════════════════════════════════════════════╗
                    欢迎使用 {config.APP_NAME}                    
╚═══════════════════════════════════════════════════════════╝

💡 快速开始
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • 输入产品号查询图纸
  • 查询成功后，右侧大区域嵌入显示PDF（滚轮滚动，+/- 按钮缩放）
  • 在"数据管理"标签页进行增删改查

📊 系统信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  版本: {config.APP_NAME} v{config.VERSION}
  环境: {'开发' if config.DEBUG else '生产'}
  数据库: {config.DB_NAME} @ {config.DB_HOST}

═══════════════════════════════════════════════════════════════
        """
        self.info_display.setText(welcome_text)
        self.pdf_viewer.clear()
        self.status_bar.showMessage("就绪 - 请输入产品号查询", 5000)
    
    def search_drawing(self):
        """查询图纸"""
        product_code = self.code_input.text().strip()
        if not product_code:
            QMessageBox.warning(self, "提示", "请输入产品号！")
            return
        
        self.search_btn.setEnabled(False)
        self.status_bar.showMessage("正在查询...")
        
        # 查询
        self.current_drawing = db_manager.search_by_code(product_code)
        
        if self.current_drawing:
            full_path = pdf_handler.get_full_path(self.current_drawing['pdf_path'])
            self.display_drawing_info(self.current_drawing)
            # 加载嵌入PDF（替换外部打开）
            if self.pdf_viewer.load_pdf(full_path):
                self.status_bar.showMessage(f"PDF加载成功: {product_code}", 3000)
            else:
                self.status_bar.showMessage("PDF加载失败 - 文件不存在", 3000)
                # 如果加载失败，可选：调用外部打开作为回退
                # success, msg = pdf_handler.open_pdf(self.current_drawing['pdf_path'])
                # if not success:
                #     QMessageBox.critical(self, "错误", msg)
        else:
            self.current_drawing = None
            self.display_not_found(product_code)
            self.pdf_viewer.clear()
            self.status_bar.showMessage(f"未找到图纸: {product_code}", 3000)
        
        self.search_btn.setEnabled(True)
    
    def display_drawing_info(self, drawing):
        """显示图纸信息"""
        full_path = pdf_handler.get_full_path(drawing['pdf_path'])
        info_text = f"""
╔═══════════════════════════════════════════════════════════╗
                    查询成功 - 图纸信息                    
╚═══════════════════════════════════════════════════════════╝

📋 基本信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ID:         {drawing['id']}
  产品号:     {drawing['product_code']}
  PDF路径:    {drawing['pdf_path']}

📂 完整路径
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {full_path}

💡 操作提示
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • 右侧大区域显示PDF，支持滚轮滚动和缩放
  • Ctrl+滚轮快速缩放

═══════════════════════════════════════════════════════════════
        """
        self.info_display.setText(info_text)
    
    def display_not_found(self, product_code):
        """显示未找到信息"""
        not_found_text = f"""
╔═══════════════════════════════════════════════════════════╗
                        未找到图纸                        
╚═══════════════════════════════════════════════════════════╝

❌ 查询结果
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  未找到产品号为 '{product_code}' 的图纸

💡 建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. 检查产品号是否正确
  2. 确认产品号区分大小写
  3. 查看统计信息了解已有数据

═══════════════════════════════════════════════════════════════
        """
        self.info_display.setText(not_found_text)
    
    def show_statistics(self):
        """显示统计信息"""
        total = db_manager.get_total_count()
        
        stats_text = f"""
统计信息
━━━━━━━━━━━━━━━━━━━━━━━━━━

图纸总数: {total} 个

数据库: {config.DB_HOST}
PDF目录: {config.PDF_NETWORK_PATH}

━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        QMessageBox.information(self, "统计信息", stats_text)
    
    def clear_display(self):
        """清空显示"""
        self.code_input.clear()
        self.current_drawing = None
        self.pdf_viewer.clear()
        self.show_welcome()
        self.code_input.setFocus()
        self.status_bar.showMessage("已清空", 2000)
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        # Ctrl+Q 退出
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Q:
            self.close()