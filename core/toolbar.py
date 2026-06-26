"""Toolbar điều hướng: back/forward/reload/home + thanh địa chỉ + nút bookmark."""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLineEdit, QSizePolicy, QToolBar, QToolButton


class NavigationBar(QToolBar):
    back_clicked = pyqtSignal()
    forward_clicked = pyqtSignal()
    reload_clicked = pyqtSignal()
    home_clicked = pyqtSignal()
    go_requested = pyqtSignal(str)
    star_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Điều hướng", parent)
        self.setMovable(False)

        self.back_btn = QToolButton()
        self.back_btn.setText("◀")
        self.back_btn.setToolTip("Quay lại")

        self.forward_btn = QToolButton()
        self.forward_btn.setText("▶")
        self.forward_btn.setToolTip("Tiến tới")

        self.reload_btn = QToolButton()
        self.reload_btn.setText("⟳")
        self.reload_btn.setToolTip("Tải lại (F5)")

        self.home_btn = QToolButton()
        self.home_btn.setText("⌂")
        self.home_btn.setToolTip("Trang chủ")

        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText("Nhập địa chỉ web hoặc từ khóa tìm kiếm…")
        self.address_bar.setClearButtonEnabled(True)
        self.address_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.star_btn = QToolButton()
        self.star_btn.setText("☆")
        self.star_btn.setToolTip("Đánh dấu trang (Ctrl+D)")

        for w in (self.back_btn, self.forward_btn, self.reload_btn, self.home_btn,
                   self.address_bar, self.star_btn):
            self.addWidget(w)

        self.back_btn.clicked.connect(self.back_clicked.emit)
        self.forward_btn.clicked.connect(self.forward_clicked.emit)
        self.reload_btn.clicked.connect(self.reload_clicked.emit)
        self.home_btn.clicked.connect(self.home_clicked.emit)
        self.star_btn.clicked.connect(self.star_clicked.emit)
        self.address_bar.returnPressed.connect(self._emit_go)

    def _emit_go(self):
        self.go_requested.emit(self.address_bar.text().strip())

    def set_url(self, url):
        self.address_bar.setText(url)
        self.address_bar.setCursorPosition(0)

    def set_bookmarked(self, is_bookmarked):
        self.star_btn.setText("★" if is_bookmarked else "☆")

    def focus_address_bar(self):
        self.address_bar.setFocus()
        self.address_bar.selectAll()
