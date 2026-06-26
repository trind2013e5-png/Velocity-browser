"""Quản lý các tab trình duyệt (mỗi tab là 1 QWebEngineView)."""
from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QTabWidget, QToolButton


class TabManager(QTabWidget):
    # Phát ra khi tab ĐANG HIỂN THỊ có url/title thay đổi -> browser_window
    # dùng để cập nhật thanh địa chỉ / tiêu đề cửa sổ.
    url_changed = pyqtSignal(str)
    title_changed = pyqtSignal(str)
    load_progress = pyqtSignal(int)
    load_finished = pyqtSignal(object, bool)  # (view, ok)

    def __init__(self, home_url, parent=None):
        super().__init__(parent)
        self.home_url = home_url
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)

        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self._on_current_changed)

        new_tab_btn = QToolButton()
        new_tab_btn.setText("+")
        new_tab_btn.setToolTip("Tab mới (Ctrl+T)")
        new_tab_btn.clicked.connect(lambda: self.new_tab())
        self.setCornerWidget(new_tab_btn)

    def new_tab(self, url=None):
        view = QWebEngineView()
        view.setUrl(QUrl(url or self.home_url))
        index = self.addTab(view, "Tab mới")
        self.setCurrentIndex(index)

        view.urlChanged.connect(lambda qurl, v=view: self._on_url_changed(v, qurl))
        view.titleChanged.connect(lambda title, v=view: self._on_title_changed(v, title))
        view.iconChanged.connect(lambda icon, v=view: self._on_icon_changed(v, icon))
        view.loadProgress.connect(self._on_load_progress)
        view.loadFinished.connect(lambda ok, v=view: self.load_finished.emit(v, ok))
        return view

    def close_tab(self, index):
        # Giữ lại tối thiểu 1 tab để không bị trống cửa sổ
        if self.count() <= 1:
            return
        widget = self.widget(index)
        self.removeTab(index)
        if widget:
            widget.deleteLater()

    def current_view(self):
        return self.currentWidget()

    def _on_current_changed(self, index):
        view = self.widget(index)
        if view is not None:
            self.url_changed.emit(view.url().toString())
            self.title_changed.emit(view.title())

    def _on_url_changed(self, view, qurl):
        if view is self.current_view():
            self.url_changed.emit(qurl.toString())

    def _on_title_changed(self, view, title):
        index = self.indexOf(view)
        if index != -1:
            short = (title[:24] + "…") if title and len(title) > 24 else (title or "Tab mới")
            self.setTabText(index, short)
        if view is self.current_view():
            self.title_changed.emit(title)

    def _on_icon_changed(self, view, icon):
        index = self.indexOf(view)
        if index != -1 and not icon.isNull():
            self.setTabIcon(index, icon)

    def _on_load_progress(self, value):
        self.load_progress.emit(value)
