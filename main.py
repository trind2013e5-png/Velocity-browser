"""
PyBrowser - trình duyệt viết bằng PyQt6.
Chạy: python main.py
"""
import sys

from PyQt6.QtWidgets import QApplication

from core.browser_window import BrowserWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PyBrowser")
    app.setOrganizationName("PyBrowser")

    window = BrowserWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
