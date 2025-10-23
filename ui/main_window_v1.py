"""
主窗口界面
图纸查询系统的主界面
"""
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
        query_layout = QVBoxLayout()
        query_tab.setLayout(query_layout)
        
        # 标题
        title_label = QLabel(config.APP_NAME)
        title_label.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; padding: 20px;")
        query_layout.addWidget(title_label)
        
        # 搜索区域
        search_group = QGroupBox("快速查询")
        search_group.setFont(QFont("Microsoft YaHei", 11))
        search_layout = QHBoxLayout()
        
        # 标签
        label = QLabel("产品号:")
        label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        search_layout.addWidget(label)
        
        # 输入框
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("请输入产品号，按回车查询...")
        self.code_input.setFont(QFont("Microsoft YaHei", 14))
        self.code_input.setMinimumHeight(40)
        self.code_input.returnPressed.connect(self.search_drawing)  # 回车触发查询
        search_layout.addWidget(self.code_input, 3)
        
        # 查询按钮
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
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.search_btn.clicked.connect(self.search_drawing)
        search_layout.addWidget(self.search_btn)
        
        search_group.setLayout(search_layout)
        query_layout.addWidget(search_group)
        
        # 打开PDF按钮（移到搜索组下）
        open_layout = QHBoxLayout()
        self.open_btn = QPushButton("打开图纸")
        self.open_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.open_btn.setMinimumHeight(40)
        self.open_btn.setMinimumWidth(120)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.open_btn.clicked.connect(self.open_pdf)
        self.open_btn.setEnabled(False)
        open_layout.addStretch()
        open_layout.addWidget(self.open_btn)
        open_layout.addStretch()
        query_layout.addLayout(open_layout)
        
        # 信息显示
        self.info_display = QTextEdit()
        self.info_display.setFont(QFont("Microsoft YaHei", 10))
        self.info_display.setReadOnly(True)
        self.info_display.setStyleSheet("background-color: #f8f9fa; border: 1px solid #bdc3c7; border-radius: 5px; padding: 10px;")
        self.info_display.setMinimumHeight(300)
        query_layout.addWidget(self.info_display)
        
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
        query_layout.addLayout(op_layout)
        
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
  • 在"快速查询"标签页输入产品号查询图纸
  • 点击"打开图纸"使用默认阅读器查看PDF
  • 在"数据管理"标签页进行增删改查操作

📊 系统信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  版本: {config.APP_NAME} v{config.VERSION}
  环境: {'开发' if config.DEBUG else '生产'}
  数据库: {config.DB_NAME} @ {config.DB_HOST}

═══════════════════════════════════════════════════════════════
        """
        self.info_display.setText(welcome_text)
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
            self.display_drawing_info(self.current_drawing)
            self.open_btn.setEnabled(True)
            self.status_bar.showMessage(f"找到图纸: {product_code}", 3000)
        else:
            self.current_drawing = None
            self.display_not_found(product_code)
            self.open_btn.setEnabled(False)
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
  • 点击"打开图纸"按钮查看PDF
  • 或继续输入其他产品号查询

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
    
    def open_pdf(self):
        """打开PDF文件"""
        if not self.current_drawing:
            QMessageBox.warning(self, "提示", "请先查询图纸！")
            return
        
        # 获取PDF路径
        pdf_path = self.current_drawing['pdf_path']
        
        # 打开PDF
        self.status_bar.showMessage("正在打开PDF...")
        success, message = pdf_handler.open_pdf(pdf_path)
        
        if success:
            self.status_bar.showMessage(f"已打开: {pdf_path}", 3000)
            QMessageBox.information(
                self, 
                "成功", 
                f"已使用系统默认PDF阅读器打开:\n{pdf_path}"
            )
        else:
            self.status_bar.showMessage("打开失败", 3000)
            QMessageBox.critical(self, "错误", message)
    
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
        self.open_btn.setEnabled(False)
        self.show_welcome()
        self.code_input.setFocus()
        self.status_bar.showMessage("已清空", 2000)
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        # Ctrl+Q 退出
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Q:
            self.close()