"""Cửa sổ chính của PyBrowser: ghép toolbar, tab manager, menu, adblock, dark mode."""
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineScript
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStatusBar

from core import dark_mode
from core.adblock import AdBlocker
from core.bookmarks import BookmarkManager
from core.dialogs import BookmarksDialog, HistoryDialog
from core.history import HistoryManager
from core.settings_manager import SettingsManager
from core.tab_manager import TabManager
from core.toolbar import NavigationBar
from core.utils import resolve_url


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyBrowser")
        self.resize(1280, 800)

        # ----- dữ liệu / cấu hình -----
        self.settings = SettingsManager()
        self.bookmarks = BookmarkManager()
        self.history = HistoryManager()

        # ----- web engine profile + adblock -----
        self.profile = QWebEngineProfile.defaultProfile()
        self.adblocker = AdBlocker(self)
        self.adblocker.enabled = self.settings.get("adblock_enabled", True)
        self.profile.setUrlRequestInterceptor(self.adblocker)

        self._dark_script = None
        if self.settings.get("dark_mode", False):
            self._enable_dark_script()

        # ----- UI -----
        self.nav_bar = NavigationBar(self)
        self.addToolBar(self.nav_bar)

        self.tabs = TabManager(self.settings.get("home_page"), self)
        self.setCentralWidget(self.tabs)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self._build_menu()
        self._build_shortcuts()
        self._connect_signals()

        self.tabs.new_tab()
        self._apply_theme()

    # ================= MENU =================
    def _build_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Tệp")
        act_new_tab = QAction("Tab mới", self)
        act_new_tab.setShortcut(QKeySequence("Ctrl+T"))
        act_new_tab.triggered.connect(lambda: self.tabs.new_tab())
        act_close_tab = QAction("Đóng tab", self)
        act_close_tab.setShortcut(QKeySequence("Ctrl+W"))
        act_close_tab.triggered.connect(lambda: self.tabs.close_tab(self.tabs.currentIndex()))
        act_exit = QAction("Thoát", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_new_tab)
        file_menu.addAction(act_close_tab)
        file_menu.addSeparator()
        file_menu.addAction(act_exit)

        self.bookmarks_menu = menubar.addMenu("Bookmark")
        self._rebuild_bookmarks_menu()

        history_menu = menubar.addMenu("Lịch sử")
        act_show_history = QAction("Xem lịch sử", self)
        act_show_history.triggered.connect(self._show_history)
        act_clear_history = QAction("Xóa lịch sử", self)
        act_clear_history.triggered.connect(self._clear_history)
        history_menu.addAction(act_show_history)
        history_menu.addAction(act_clear_history)

        view_menu = menubar.addMenu("Xem")
        self.act_dark_mode = QAction("Dark mode", self, checkable=True)
        self.act_dark_mode.setChecked(self.settings.get("dark_mode", False))
        self.act_dark_mode.toggled.connect(self._toggle_dark_mode)
        self.act_adblock = QAction("Chặn quảng cáo", self, checkable=True)
        self.act_adblock.setChecked(self.settings.get("adblock_enabled", True))
        self.act_adblock.toggled.connect(self._toggle_adblock)
        view_menu.addAction(self.act_dark_mode)
        view_menu.addAction(self.act_adblock)

        help_menu = menubar.addMenu("Trợ giúp")
        act_about = QAction("Giới thiệu", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _rebuild_bookmarks_menu(self):
        self.bookmarks_menu.clear()
        act_manage = QAction("Quản lý bookmark…", self)
        act_manage.triggered.connect(self._show_bookmarks)
        self.bookmarks_menu.addAction(act_manage)
        self.bookmarks_menu.addSeparator()
        for item in self.bookmarks.all():
            act = QAction(item["title"] or item["url"], self)
            act.triggered.connect(lambda checked=False, u=item["url"]: self._navigate(u))
            self.bookmarks_menu.addAction(act)

    def _build_shortcuts(self):
        act_focus_address = QAction(self)
        act_focus_address.setShortcut(QKeySequence("Ctrl+L"))
        act_focus_address.triggered.connect(self.nav_bar.focus_address_bar)
        self.addAction(act_focus_address)

        act_bookmark = QAction(self)
        act_bookmark.setShortcut(QKeySequence("Ctrl+D"))
        act_bookmark.triggered.connect(self._toggle_bookmark)
        self.addAction(act_bookmark)

        act_reload = QAction(self)
        act_reload.setShortcut(QKeySequence("F5"))
        act_reload.triggered.connect(lambda: self.tabs.current_view() and self.tabs.current_view().reload())
        self.addAction(act_reload)

    # ================= SIGNALS =================
    def _connect_signals(self):
        self.nav_bar.back_clicked.connect(lambda: self.tabs.current_view() and self.tabs.current_view().back())
        self.nav_bar.forward_clicked.connect(lambda: self.tabs.current_view() and self.tabs.current_view().forward())
        self.nav_bar.reload_clicked.connect(lambda: self.tabs.current_view() and self.tabs.current_view().reload())
        self.nav_bar.home_clicked.connect(lambda: self._navigate(self.settings.get("home_page")))
        self.nav_bar.go_requested.connect(self._navigate)
        self.nav_bar.star_clicked.connect(self._toggle_bookmark)

        self.tabs.url_changed.connect(self._on_url_changed)
        self.tabs.title_changed.connect(self._on_title_changed)
        self.tabs.currentChanged.connect(lambda _i: self._wire_current_view())
        self.tabs.load_finished.connect(self._on_load_finished)

    def _wire_current_view(self):
        view = self.tabs.current_view()
        if view:
            self.nav_bar.set_url(view.url().toString())
            self.nav_bar.set_bookmarked(self.bookmarks.is_bookmarked(view.url().toString()))

    # ================= NAVIGATION =================
    def _navigate(self, text):
        url = resolve_url(text, self.settings.get("search_engine"))
        if not url:
            return
        view = self.tabs.current_view()
        if view is None:
            self.tabs.new_tab(url)
        else:
            view.setUrl(QUrl(url))

    def _on_url_changed(self, url):
        self.nav_bar.set_url(url)
        self.nav_bar.set_bookmarked(self.bookmarks.is_bookmarked(url))

    def _on_title_changed(self, title):
        self.setWindowTitle(f"{title} - PyBrowser" if title else "PyBrowser")

    def _on_load_finished(self, view, ok):
        if ok:
            self.history.add(view.url().toString(), view.title())
        self.status.showMessage(
            f"Đã chặn {self.adblocker.blocked_count} request quảng cáo/theo dõi (tổng từ lúc mở app)",
            3000,
        )

    # ================= BOOKMARK =================
    def _toggle_bookmark(self):
        view = self.tabs.current_view()
        if not view:
            return
        url = view.url().toString()
        is_bm = self.bookmarks.toggle(url, view.title())
        self.nav_bar.set_bookmarked(is_bm)
        self._rebuild_bookmarks_menu()

    def _show_bookmarks(self):
        dlg = BookmarksDialog(self.bookmarks, self)
        dlg.open_requested.connect(self._navigate)
        dlg.exec()
        self._rebuild_bookmarks_menu()
        self._wire_current_view()

    # ================= HISTORY =================
    def _show_history(self):
        dlg = HistoryDialog(self.history, self)
        dlg.open_requested.connect(self._navigate)
        dlg.exec()

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "Xóa lịch sử", "Xóa toàn bộ lịch sử trình duyệt?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history.clear()

    # ================= DARK MODE =================
    def _enable_dark_script(self):
        script = QWebEngineScript()
        script.setName("pybrowser_dark_mode")
        script.setSourceCode(dark_mode.DARK_CSS_INJECT_JS)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
        script.setRunsOnSubFrames(True)
        self.profile.scripts().insert(script)
        self._dark_script = script

    def _disable_dark_script(self):
        if self._dark_script is not None:
            self.profile.scripts().remove(self._dark_script)
            self._dark_script = None

    def _toggle_dark_mode(self, checked):
        self.settings.set("dark_mode", checked)
        if checked:
            self._enable_dark_script()
        else:
            self._disable_dark_script()

        # áp dụng ngay cho các tab đang mở (script profile chỉ chạy cho trang load mới)
        js = dark_mode.DARK_CSS_INJECT_JS if checked else dark_mode.DARK_CSS_REMOVE_JS
        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)
            if view:
                view.page().runJavaScript(js)
        self._apply_theme()

    def _apply_theme(self):
        if self.settings.get("dark_mode", False):
            self.setStyleSheet(dark_mode.APP_DARK_STYLESHEET)
        else:
            self.setStyleSheet(dark_mode.APP_LIGHT_STYLESHEET)

    # ================= ADBLOCK =================
    def _toggle_adblock(self, checked):
        self.settings.set("adblock_enabled", checked)
        self.adblocker.enabled = checked

    # ================= ABOUT =================
    def _show_about(self):
        QMessageBox.information(
            self,
            "Giới thiệu",
            "PyBrowser\n\n"
            "Trình duyệt viết bằng PyQt6, dùng QWebEngine (Chromium) để render web.\n"
            "Toàn bộ giao diện và tính năng (tab, bookmark, lịch sử, chặn quảng cáo,\n"
            "dark mode) là code Python thuần trong thư mục core/, dễ đọc và tùy biến.",
        )
