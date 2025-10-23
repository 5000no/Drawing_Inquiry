"""
PDF查看器小部件
嵌入式显示PDF，支持缩放和滚动
"""
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView


class PDFViewer(QWidget):
    """PDF查看器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_factor = 1.0  # 当前缩放比例
        self.min_zoom = 0.5
        self.max_zoom = 3.0
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 缩放控制按钮（顶部小栏）
        control_layout = QHBoxLayout()
        zoom_label = QLabel("缩放:")
        zoom_label.setFont(QFont("Microsoft YaHei", 9))
        control_layout.addWidget(zoom_label)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(30, 25)
        self.zoom_in_btn.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; border: none; border-radius: 3px; font-weight: bold; }
            QPushButton:hover { background-color: #229954; }
        """)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        control_layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedSize(30, 25)
        self.zoom_out_btn.setStyleSheet("""
            QPushButton { background-color: #e74c3c; color: white; border: none; border-radius: 3px; font-weight: bold; }
            QPushButton:hover { background-color: #c0392b; }
        """)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        control_layout.addWidget(self.zoom_out_btn)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFont(QFont("Microsoft YaHei", 9))
        control_layout.addWidget(self.zoom_label)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # PDF查看器
        self.web_view = QWebEngineView()
        self.web_view.setZoomFactor(self.zoom_factor)
        
        layout.addWidget(self.web_view)
        self.setLayout(layout)
        self.hide()  # 初始隐藏
    
    def load_pdf(self, pdf_full_path):
        """加载PDF文件"""
        if not pdf_full_path or not os.path.exists(pdf_full_path):
            print(f"❌ PDF路径不存在: {pdf_full_path}")  # 调试输出
            return False
        url = QUrl.fromLocalFile(pdf_full_path)
        self.web_view.load(url)
        self.show()
        print(f"✅ PDF加载成功: {pdf_full_path}")  # 调试输出
        return True
    
    def zoom_in(self):
        """放大"""
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor += 0.2
            self.web_view.setZoomFactor(self.zoom_factor)
            self.update_zoom_label()
    
    def zoom_out(self):
        """缩小"""
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor -= 0.2
            self.web_view.setZoomFactor(self.zoom_factor)
            self.update_zoom_label()
    
    def reset_zoom(self):
        """重置缩放"""
        self.zoom_factor = 1.0
        self.web_view.setZoomFactor(self.zoom_factor)
        self.update_zoom_label()
    
    def update_zoom_label(self):
        """更新缩放标签"""
        self.zoom_label.setText(f"{int(self.zoom_factor * 100)}%")
    
    def clear(self):
        """清空PDF"""
        self.web_view.setUrl(QUrl())
        self.hide()
        self.reset_zoom()