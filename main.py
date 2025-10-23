"""
图纸查询系统 - 主程序入口
"""
import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window_v1 import MainWindow


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()