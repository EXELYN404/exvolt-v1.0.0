"""
EXVOLT — Main Application Shell
Redesigned cybersecurity desktop application with premium dark glassmorphism UI.
Preserves all original VersSuite backend functionality and callbacks.
"""
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QStackedWidget, QStatusBar, QFrame, QDialog, QTextEdit, QSplitter,
    QAction, QMenuBar, QMessageBox, QFileDialog, QShortcut
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence, QDesktopServices

from core import (
    ProxyServer, cert_exists, get_install_instructions, open_cert_dir,
    load_config, save_config, APP_VERSION, APP_AUTHOR, REPO_URL,
    check_for_updates, ScopeManager, MatchReplaceEngine, save_session, load_session,
)
from .design_tokens import (
    BACKGROUND, SURFACE, SURFACE_ELEVATED, TEAL_PRIMARY, CYAN_PRIMARY,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER, BORDER_TEAL,
    SUCCESS, DANGER, INFO, FONT_SANS, FONT_MONO,
    SIDEBAR_WIDTH, HEADER_HEIGHT, STATUS_BAR_HEIGHT,
)
from .components import (
    GlassCard, SectionHeader, MetricCard, StatusBadge, IconButton,
    PrimaryButton, SecondaryButton, Toolbar, DarkTable, DarkEditor,
    ProgressIndicator, EmptyState, SidebarItem, PageHeader,
)
from .sidebar import Sidebar
from .header import Header

# Page imports (original functionality, new UI wrappers)
from .pages.proxy_page import ProxyPage
from .pages.history_page import HistoryPage
from .pages.repeater_page import RepeaterPage
from .pages.intruder_page import IntruderPage
from .pages.comparer_page import ComparerPage
from .pages.sequencer_page import SequencerPage
from .pages.websocket_page import WebSocketPage
from .pages.decoder_page import DecoderPage
from .pages.about_page import AboutPage

# Dialogs (original, unchanged)
from .scope_dialog import ScopeDialog
from .match_replace_dialog import MatchReplaceDialog


class CertDialog(QDialog):
    """Certificate installation dialog (original, unchanged)."""

    def __init__(self, proxy_host: str = "127.0.0.1", proxy_port: int = 8080, parent=None):
        super().__init__(parent)
        self.setWindowTitle("EXVOLT — CA Certificate Setup")
        self.setMinimumWidth(620)
        self.setMinimumHeight(400)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel("🔒 Install CA Certificate for HTTPS Interception")
        title.setStyleSheet(f"font-size:15px; font-weight:700; color:{TEAL_PRIMARY};")
        layout.addWidget(title)
        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setPlainText(get_install_instructions(proxy_host, proxy_port))
        instructions.setStyleSheet(
            f"background:{BACKGROUND}; color:{TEXT_SECONDARY}; "
            f"font-family: '{FONT_MONO}'; font-size:12px;"
        )
        layout.addWidget(instructions)
        btn_bar = QHBoxLayout()
        btn_open = QPushButton("📂 Open Certificate Folder")
        btn_open.clicked.connect(open_cert_dir)
        btn_bar.addWidget(btn_open)
        btn_bar.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_bar.addWidget(btn_close)
        layout.addLayout(btn_bar)


class UpdateCheckWorker(QObject):
    finished = pyqtSignal(object)

    def run(self):
        result = check_for_updates(APP_VERSION)
        self.finished.emit(result)


class MainWindow(QMainWindow):
    """
    EXVOLT Main Window.
    Shell: Sidebar | Header | Stacked Workspace | Status Bar.
    All original backend connections and callbacks are preserved.
    """

    def __init__(self):
        super().__init__()

        # ── Backend (unchanged) ──
        self.scope_manager = ScopeManager()
        self.match_replace_engine = MatchReplaceEngine()
        self.proxy = ProxyServer()
        self.proxy.scope_manager = self.scope_manager
        self.proxy.match_replace_engine = self.match_replace_engine

        self._req_count = 0
        self._update_thread = None
        self._update_worker = None

        # ── UI ──
        self._setup_ui()
        self._setup_connections()
        self._setup_shortcuts()
        self._apply_config()

        # Poll proxy event queue (80 ms) — original behavior preserved
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_proxy_events)
        self._poll_timer.start(80)

    # ════════════════════════════════════════════════════════════════════════════
    # UI SETUP
    # ════════════════════════════════════════════════════════════════════════════

    def _setup_ui(self):
        self.setWindowTitle(f"EXVOLT · v{APP_VERSION} · by {APP_AUTHOR}")
        self.setMinimumSize(1200, 780)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Menus ──
        self._build_menus()

        # ── Header ──
        self.header = Header()
        root.addWidget(self.header)

        # ── Body: Sidebar + Workspace ──
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_page_changed)
        body.addWidget(self.sidebar)

        self.workspace = QStackedWidget()
        body.addWidget(self.workspace, stretch=1)

        root.addLayout(body, stretch=1)

        # ── Status bar ──
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(
            f"QStatusBar {{ background: {BACKGROUND}; color: {TEXT_MUTED}; "
            f"border-top: 1px solid {BORDER}; font-size: 11px; }}"
        )
        self.lbl_proxy_status = QLabel(" ⬤ Proxy: Stopped")
        self.lbl_proxy_status.setStyleSheet(f"color: {DANGER};")
        self.lbl_intercept_status = QLabel(" Intercept: Off")
        self.lbl_intercept_status.setStyleSheet(f"color: {TEXT_MUTED};")
        self.lbl_req_count = QLabel(" Requests: 0")
        self.lbl_req_count.setStyleSheet(f"color: {TEXT_MUTED};")
        self.status_bar.addWidget(self.lbl_proxy_status)
        self.status_bar.addWidget(QLabel(" | "))
        self.status_bar.addWidget(self.lbl_intercept_status)
        self.status_bar.addWidget(QLabel(" | "))
        self.status_bar.addWidget(self.lbl_req_count)
        self.setStatusBar(self.status_bar)

        # ── Pages ──
        self._build_pages()

        # Show proxy page by default
        self.sidebar.set_active("proxy")
        self.workspace.setCurrentWidget(self.proxy_page)
        self.header.set_page_title("Proxy / Intercept")

    def _build_pages(self):
        """Instantiate all page widgets and add to the stacked workspace."""
        self.proxy_page = ProxyPage(self.proxy, self.scope_manager, self.match_replace_engine)
        self.history_page = HistoryPage(self.proxy, self.scope_manager)
        self.repeater_page = RepeaterPage()
        self.intruder_page = IntruderPage()
        self.comparer_page = ComparerPage()
        self.sequencer_page = SequencerPage()
        self.websocket_page = WebSocketPage()
        self.decoder_page = DecoderPage()
        self.about_page = AboutPage(APP_VERSION, APP_AUTHOR, REPO_URL)

        for page in (
            self.proxy_page, self.history_page, self.repeater_page,
            self.intruder_page, self.comparer_page, self.sequencer_page,
            self.websocket_page, self.decoder_page, self.about_page,
        ):
            self.workspace.addWidget(page)

    # ════════════════════════════════════════════════════════════════════════════
    # MENUS
    # ════════════════════════════════════════════════════════════════════════════

    def _build_menus(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        save_act = QAction("Save Session\tCtrl+S", self)
        save_act.triggered.connect(self._save_session)
        file_menu.addAction(save_act)
        load_act = QAction("Load Session\tCtrl+O", self)
        load_act.triggered.connect(self._load_session)
        file_menu.addAction(load_act)
        file_menu.addSeparator()
        exit_act = QAction("Exit", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        project_menu = menubar.addMenu("&Project")
        scope_act = QAction("Target Scope", self)
        scope_act.triggered.connect(self._show_scope_dialog)
        project_menu.addAction(scope_act)
        rules_act = QAction("Match && Replace Rules", self)
        rules_act.triggered.connect(self._show_match_replace_dialog)
        project_menu.addAction(rules_act)

        help_menu = menubar.addMenu("&Help")
        cert_act = QAction("Install CA Certificate", self)
        cert_act.triggered.connect(self._show_cert_dialog)
        help_menu.addAction(cert_act)
        changelogs_act = QAction("Changelogs", self)
        changelogs_act.triggered.connect(self._show_changelogs)
        help_menu.addAction(changelogs_act)
        update_act = QAction("Check for Updates", self)
        update_act.triggered.connect(self._on_check_update)
        help_menu.addAction(update_act)

    # ════════════════════════════════════════════════════════════════════════════
    # CONNECTIONS
    # ════════════════════════════════════════════════════════════════════════════

    def _setup_connections(self):
        # ── Header → Proxy ──
        self.header.start_proxy.connect(self._on_start_proxy)
        self.header.stop_proxy.connect(self._on_stop_proxy)
        self.header.toggle_intercept.connect(self._on_intercept_toggle)
        self.header.toggle_response_intercept.connect(self._on_response_intercept_toggle)
        self.header.search_changed.connect(self._on_global_search)

        # ── Sidebar → Page switching ──
        # (handled by _on_page_changed)

        # ── Page → MainWindow signals ──
        self.proxy_page.send_to_repeater.connect(self._on_send_to_repeater)
        self.proxy_page.send_to_intruder.connect(self._on_send_to_intruder)
        self.history_page.send_to_repeater.connect(self._on_send_to_repeater)
        self.history_page.send_to_intruder.connect(self._on_send_to_intruder)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self._save_session)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self._load_session)

    # ════════════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ════════════════════════════════════════════════════════════════════════════

    def _on_page_changed(self, key: str):
        page_map = {
            "proxy": self.proxy_page,
            "history": self.history_page,
            "repeater": self.repeater_page,
            "intruder": self.intruder_page,
            "comparer": self.comparer_page,
            "sequencer": self.sequencer_page,
            "websocket": self.websocket_page,
            "decoder": self.decoder_page,
            "about": self.about_page,
            "settings": None,
        }
        page = page_map.get(key)
        if page is None:
            # Settings not implemented as a separate page; fall back to proxy
            page = self.proxy_page
            key = "proxy"
        self.workspace.setCurrentWidget(page)
        title_map = {
            "proxy": "Proxy / Intercept",
            "history": "HTTP History",
            "repeater": "Repeater",
            "intruder": "Intruder",
            "comparer": "Comparer",
            "sequencer": "Sequencer",
            "websocket": "WebSocket",
            "decoder": "Decoder",
            "about": "About",
        }
        self.header.set_page_title(title_map.get(key, "Dashboard"))

    # ════════════════════════════════════════════════════════════════════════════
    # PROXY LIFECYCLE (original callbacks preserved)
    # ════════════════════════════════════════════════════════════════════════════

    def _on_start_proxy(self, host: str, port: int):
        self.proxy.start(host, port)
        self.header.set_proxy_running(True)
        self.lbl_proxy_status.setText(" ⬤ Proxy: Running")
        self.lbl_proxy_status.setStyleSheet(f"color: {SUCCESS};")

    def _on_stop_proxy(self):
        self.proxy.stop()
        self.header.set_proxy_running(False)
        self.lbl_proxy_status.setText(" ⬤ Proxy: Stopped")
        self.lbl_proxy_status.setStyleSheet(f"color: {DANGER};")

    def _on_intercept_toggle(self, checked: bool):
        self.proxy.intercept_enabled.set() if checked else self.proxy.intercept_enabled.clear()
        self.header.set_intercept(checked)
        self.lbl_intercept_status.setText(f" Intercept: {'On' if checked else 'Off'}")
        self.lbl_intercept_status.setStyleSheet(
            f"color: {TEAL_PRIMARY if checked else TEXT_MUTED};"
        )

    def _on_response_intercept_toggle(self, checked: bool):
        self.proxy.response_intercept_enabled.set() if checked else self.proxy.response_intercept_enabled.clear()
        self.header.set_response_intercept(checked)

    def _on_global_search(self, text: str):
        # Global search: forward to the active page if it supports filtering
        page = self.workspace.currentWidget()
        if hasattr(page, "set_filter_text"):
            page.set_filter_text(text)

    # ════════════════════════════════════════════════════════════════════════════
    # PROXY EVENT POLLING (original behavior preserved)
    # ════════════════════════════════════════════════════════════════════════════

    def _poll_proxy_events(self):
        try:
            while True:
                event = self.proxy.event_queue.get_nowait()
                self._handle_proxy_event(event)
        except Exception:
            pass  # Queue empty

    def _handle_proxy_event(self, event: dict):
        etype = event.get("type")
        if etype == "proxy_started":
            self.header.set_proxy_running(True)
            self.lbl_proxy_status.setText(" ⬤ Proxy: Running")
            self.lbl_proxy_status.setStyleSheet(f"color: {SUCCESS};")
        elif etype == "intercept":
            self.proxy_page.show_intercepted(event)
            self._req_count += 1
            self.lbl_req_count.setText(f" Requests: {self._req_count}")
        elif etype == "history":
            self.history_page.add_request(event)
            self._req_count += 1
            self.lbl_req_count.setText(f" Requests: {self._req_count}")
        elif etype == "response":
            self.history_page.update_response(event)
            self.proxy_page.show_response(event)
        elif etype == "response_intercept":
            self.proxy_page.show_response_intercept(event)
        elif etype == "websocket":
            self.websocket_page.add_message(event)
        elif etype == "error":
            self.proxy_page.show_error(event)
        elif etype == "proxy_error":
            self.header.set_proxy_running(False)
            self.lbl_proxy_status.setText(" ⬤ Proxy: Error")
            self.lbl_proxy_status.setStyleSheet(f"color: {DANGER};")

    # ════════════════════════════════════════════════════════════════════════════
    # PAGE ACTIONS (send to repeater / intruder)
    # ════════════════════════════════════════════════════════════════════════════

    def _on_send_to_repeater(self, raw_request: str, host_port: tuple):
        self.sidebar.set_active("repeater")
        self.workspace.setCurrentWidget(self.repeater_page)
        self.header.set_page_title("Repeater")
        self.repeater_page.load_request(raw_request, host_port)

    def _on_send_to_intruder(self, raw_request: str):
        self.sidebar.set_active("intruder")
        self.workspace.setCurrentWidget(self.intruder_page)
        self.header.set_page_title("Intruder")
        self.intruder_page.load_request(raw_request)

    # ════════════════════════════════════════════════════════════════════════════
    # SESSION / MENU ACTIONS (original, unchanged)
    # ════════════════════════════════════════════════════════════════════════════

    def _save_session(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Session", "session.verssuite", "EXVOLT Session (*.verssuite)"
        )
        if not path:
            return
        data = {
            "history_flows": self.history_page.get_flows(),
            "history_responses": self.history_page.get_responses(),
            "history_notes": self.history_page.get_notes(),
            "repeater_sessions": self.repeater_page.get_sessions(),
            "intruder_results": self.intruder_page.get_results(),
            "scope_rules": self.scope_manager.to_list(),
            "scope_enabled": self.scope_manager.enabled,
            "match_replace_rules": self.match_replace_engine.to_list(),
            "match_replace_enabled": self.match_replace_engine.enabled,
            "config": {"host": self.header.host(), "port": self.header.port()},
        }
        save_session(path, data)

    def _load_session(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Session", "", "EXVOLT Session (*.verssuite)"
        )
        if not path:
            return
        data = load_session(path)
        if not data:
            return
        self.history_page.load_session_data(data)
        self.repeater_page.load_sessions(data.get("repeater_sessions", []))
        self.intruder_page.load_results(data.get("intruder_results", []))
        self.scope_manager.load_from_list(data.get("scope_rules", []))
        self.scope_manager.enabled = data.get("scope_enabled", False)
        self.match_replace_engine.load_from_list(data.get("match_replace_rules", []))
        self.match_replace_engine.enabled = data.get("match_replace_enabled", False)
        cfg = data.get("config", {})
        if cfg:
            self.header.host_input.setText(cfg.get("host", "127.0.0.1"))
            self.header.port_input.setValue(cfg.get("port", 8080))

    def _show_scope_dialog(self):
        dlg = ScopeDialog(self.scope_manager, self)
        dlg.exec_()

    def _show_match_replace_dialog(self):
        dlg = MatchReplaceDialog(self.match_replace_engine, self)
        dlg.exec_()

    def _show_cert_dialog(self):
        dlg = CertDialog(self.header.host(), self.header.port(), self)
        dlg.exec_()

    def _show_changelogs(self):
        changelogs_text = (
            "What's New in EXVOLT\n"
            "\n"
            "• Complete UI redesign: premium dark glassmorphism with neon teal accents\n"
            "• Compact icon-only sidebar navigation\n"
            "• Redesigned header with proxy controls and status\n"
            "• All VersSuite functionality preserved: Proxy, Repeater, Intruder, Comparer,\n"
            "  Sequencer, WebSocket, Decoder, History\n"
            "• No backend changes — original proxy engine and logic intact\n"
        )
        box = QMessageBox(self)
        box.setWindowTitle("EXVOLT — Changelogs")
        box.setText(changelogs_text)
        box.exec_()

    def _on_check_update(self):
        self._update_thread = QThread()
        self._update_worker = UpdateCheckWorker()
        self._update_worker.moveToThread(self._update_thread)
        self._update_thread.started.connect(self._update_worker.run)
        self._update_worker.finished.connect(self._on_update_result)
        self._update_worker.finished.connect(self._update_thread.quit)
        self._update_thread.start()

    def _on_update_result(self, result: dict):
        status = result.get("status", "error")
        if status == "update-available":
            msg = f"Update available: {result.get('latest_version')} (current: {result.get('current_version')})"
        elif status == "up-to-date":
            msg = f"You are using the latest version ({result.get('current_version')})."
        else:
            msg = f"Update check failed: {result.get('message')}"
        QMessageBox.information(self, "EXVOLT — Update Check", msg)

    def _apply_config(self):
        cfg = load_config()
        self.header.host_input.setText(cfg.get("host", "127.0.0.1"))
        self.header.port_input.setValue(cfg.get("port", 8080))
        self.header.set_intercept(cfg.get("intercept_enabled", False))
        self.header.set_response_intercept(cfg.get("response_intercept_enabled", False))
        self.proxy.intercept_enabled.set() if cfg.get("intercept_enabled", False) else self.proxy.intercept_enabled.clear()
        self.proxy.response_intercept_enabled.set() if cfg.get("response_intercept_enabled", False) else self.proxy.response_intercept_enabled.clear()