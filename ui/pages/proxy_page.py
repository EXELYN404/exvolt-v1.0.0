"""
EXVOLT — Proxy / Intercept Page
Combines real-time request interception and HTTP history in a premium dark glassmorphism layout.
All original InterceptTab and HistoryTab functionality and callbacks are preserved.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton, QTextEdit,
    QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QLineEdit, QMessageBox, QMenu, QAction, QApplication,
    QCheckBox, QTabWidget, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter
import re

from .design_tokens import (
    BACKGROUND, SURFACE, SURFACE_ELEVATED, TEAL_PRIMARY, CYAN_PRIMARY,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER, BORDER_TEAL,
    SUCCESS, DANGER, INFO, FONT_SANS, FONT_MONO,
    RADIUS_CARD, RADIUS_INPUT, BORDER_WIDTH,
)
from ..components import (
    GlassCard, SectionHeader, StatusBadge, PrimaryButton, SecondaryButton,
    IconButton, Toolbar, DarkTable, DarkEditor, EmptyState,
)
from core.sensitive_patterns import scan_text, has_sensitive_data, get_severity_color


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP SYNTAX HIGHLIGHTER (original, unchanged)
# ═══════════════════════════════════════════════════════════════════════════════

class HttpHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self._rules = []

    def _add_rule(self, pattern, color, bold=False):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(700)
        self._rules.append((re.compile(pattern), fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ═══════════════════════════════════════════════════════════════════════════════
# PROXY PAGE
# ═══════════════════════════════════════════════════════════════════════════════

class ProxyPage(QWidget):
    """
    Proxy / Intercept workspace.
    Signals:
        send_to_repeater(str, tuple)  # (raw_request, (host, port))
        send_to_intruder(str)          # raw_request
    """

    send_to_repeater = pyqtSignal(str, tuple)
    send_to_intruder = pyqtSignal(str)

    def __init__(self, proxy, scope_manager, match_replace_engine, parent=None):
        super().__init__(parent)
        self.proxy = proxy
        self.scope_manager = scope_manager
        self.match_replace_engine = match_replace_engine

        self._flows: dict = {}
        self._responses: dict = {}
        self._notes: dict = {}
        self._order: list = []
        self._current_flow_id: str | None = None
        self._current_resp_flow_id: str | None = None
        self._dns_cache: dict = {}
        self._confirm_drop_all = True

        self._setup_ui()

    # ════════════════════════════════════════════════════════════════════════════
    # UI
    # ════════════════════════════════════════════════════════════════════════════

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Sub-tabs: Intercept | History ──
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setTabPosition(QTabWidget.North)
        self.sub_tabs.setStyleSheet(
            f"QTabBar::tab {{ padding: 6px 16px; min-width:90px; font-size:12px; "
            f"font-family: '{FONT_SANS}'; font-weight: 600; }}"
            f"QTabBar::tab:selected {{ color: {TEAL_PRIMARY}; border-bottom: 2px solid {TEAL_PRIMARY}; }}"
        )

        self.intercept_widget = self._build_intercept_panel()
        self.history_widget = self._build_history_panel()

        self.sub_tabs.addTab(self.intercept_widget, "Intercept")
        self.sub_tabs.addTab(self.history_widget, "HTTP History")

        layout.addWidget(self.sub_tabs, stretch=1)

    # ─────────────────────────────────────────────────────────────────────────
    # INTERCEPT PANEL
    # ─────────────────────────────────────────────────────────────────────────

    def _build_intercept_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # ── Top action bar ──
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        self.lbl_status = QLabel("⬤ Waiting for intercepted request…")
        self.lbl_status.setStyleSheet(f"color: {TEAL_PRIMARY}; font-weight: 600;")
        top_bar.addWidget(self.lbl_status)
        top_bar.addStretch()

        self.btn_forward = PrimaryButton("▶ Forward")
        self.btn_forward.setToolTip("Forward request (with edits if any)")
        self.btn_forward.clicked.connect(self._on_forward)
        self.btn_forward.setEnabled(False)
        top_bar.addWidget(self.btn_forward)

        self.btn_drop = SecondaryButton("✖ Drop")
        self.btn_drop.setToolTip("Drop / kill this request")
        self.btn_drop.clicked.connect(self._on_drop)
        self.btn_drop.setEnabled(False)
        top_bar.addWidget(self.btn_drop)

        self.btn_to_repeater = SecondaryButton("↗ Repeater")
        self.btn_to_repeater.setToolTip("Copy this request to the Repeater tab")
        self.btn_to_repeater.clicked.connect(self._on_send_to_repeater)
        self.btn_to_repeater.setEnabled(False)
        top_bar.addWidget(self.btn_to_repeater)

        self.btn_forward_all = SecondaryButton("≫ Forward All")
        self.btn_forward_all.setToolTip("Forward all pending intercepted requests")
        self.btn_forward_all.clicked.connect(self._on_forward_all)
        self.btn_forward_all.setEnabled(False)
        top_bar.addWidget(self.btn_forward_all)

        self.btn_drop_all = SecondaryButton("✖ Drop All")
        self.btn_drop_all.setToolTip("Drop all pending intercepted requests")
        self.btn_drop_all.clicked.connect(self._on_drop_all)
        self.btn_drop_all.setEnabled(False)
        top_bar.addWidget(self.btn_drop_all)

        self.btn_to_intruder = SecondaryButton("⚡ Intruder")
        self.btn_to_intruder.setToolTip("Copy this request to the Intruder tab")
        self.btn_to_intruder.clicked.connect(self._on_send_to_intruder)
        self.btn_to_intruder.setEnabled(False)
        top_bar.addWidget(self.btn_to_intruder)

        self.lbl_sensitive = QLabel("")
        self.lbl_sensitive.setStyleSheet(f"color: {DANGER}; font-weight: bold; font-size: 11px;")
        self.lbl_sensitive.setVisible(False)
        top_bar.addWidget(self.lbl_sensitive)

        layout.addLayout(top_bar)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {BORDER};")
        layout.addWidget(line)

        # ── Main splitter: list | editor ──
        main_splitter = QSplitter(Qt.Horizontal)

        # Pending intercepts list
        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(4)

        list_hdr = QLabel("PENDING INTERCEPTS")
        list_hdr.setStyleSheet(f"color: {TEXT_MUTED}; font-family: '{FONT_SANS}'; font-size: 10px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;")
        list_layout.addWidget(list_hdr)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter (host, path, url, method)")
        self.search_box.textChanged.connect(self._apply_filter)
        self.search_box.setStyleSheet(
            f"QLineEdit {{ background-color: {BACKGROUND}; color: {TEXT_PRIMARY}; "
            f"border: 1px solid {BORDER}; border-radius: {RADIUS_INPUT}px; padding: 4px 8px; font-size: 12px; }}"
        )
        list_layout.addWidget(self.search_box)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["#", "Method", "Host", "Path"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 140)
        self.table.currentCellChanged.connect(self._on_row_select)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_menu)
        self.table.setStyleSheet(
            f"QTableWidget {{ background-color: {SURFACE}; color: {TEXT_SECONDARY}; "
            f"border: 1px solid {BORDER}; border-radius: {RADIUS_CARD}px; }}"
            f"QTableWidget::item {{ padding: 6px 10px; border: none; }}"
            f"QTableWidget::item:selected {{ background-color: {TEAL_PRIMARY}22; color: {TEXT_PRIMARY}; }}"
            f"QHeaderView::section {{ background-color: {BACKGROUND}; color: {TEXT_MUTED}; "
            f"border: none; border-bottom: 1px solid {BORDER}; padding: 6px 10px; "
            f"font-family: '{FONT_SANS}'; font-size: 11px; font-weight: 600; text-transform: uppercase; }}"
        )
        list_layout.addWidget(self.table)
        main_splitter.addWidget(list_panel)

        # Right side: request editor + metadata
        right_splitter = QSplitter(Qt.Vertical)

        # Request panel
        req_panel = QWidget()
        req_layout = QVBoxLayout(req_panel)
        req_layout.setContentsMargins(0, 0, 0, 0)
        req_layout.setSpacing(4)

        req_hdr = QLabel("REQUEST — edit freely before forwarding")
        req_hdr.setStyleSheet(f"color: {TEXT_MUTED}; font-family: '{FONT_SANS}'; font-size: 10px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;")
        req_layout.addWidget(req_hdr)

        self.request_edit = DarkEditor(
            placeholder="Intercepted request will appear here.\nEdit it, then click ▶ Forward.",
            read_only=False,
        )
        self.request_edit.editor.setFont(QFont(FONT_MONO, 11))
        self._hl_req = HttpHighlighter(self.request_edit.editor.document())
        req_layout.addWidget(self.request_edit, stretch=1)
        right_splitter.addWidget(req_panel)

        # Info panel
        info_panel = QWidget()
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        info_hdr = QLabel("REQUEST METADATA")
        info_hdr.setStyleSheet(f"color: {TEXT_MUTED}; font-family: '{FONT_SANS}'; font-size: 10px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;")
        info_layout.addWidget(info_hdr)

        self.info_view = QTextEdit()
        self.info_view.setReadOnly(True)
        self.info_view.setMaximumHeight(100)
        self.info_view.setStyleSheet(
            f"QTextEdit {{ background-color: {BACKGROUND}; color: {TEXT_SECONDARY}; "
            f"border: 1px solid {BORDER}; border-radius: {RADIUS_INPUT}px; font-family: '{FONT_MONO}'; font-size: 11px; padding: 6px; }}"
        )
        self.info_view.setPlaceholderText("Flow metadata…")
        info_layout.addWidget(self.info_view)
        right_splitter.addWidget(info_panel)

        right_splitter.setSizes([500, 100])
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([260, 700])
        layout.addWidget(main_splitter, stretch=1)

        # ── Response Intercept Pane ──
        resp_widget = QWidget()
        resp_layout = QVBoxLayout(resp_widget)
        resp_layout.setContentsMargins(0, 8, 0, 0)
        resp_layout.setSpacing(4)

        resp_bar = QHBoxLayout()
        resp_hdr = QLabel("INTERCEPTED RESPONSE — edit before forwarding to browser")
        resp_hdr.setStyleSheet(f"color: {TEXT_MUTED}; font-family: '{FONT_SANS}'; font-size: 10px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;")
        resp_bar.addWidget(resp_hdr)
        resp_bar.addStretch()

        self.btn_resp_forward = PrimaryButton("▶ Forward Response")
        self.btn_resp_forward.clicked.connect(self._on_response_forward)
        self.btn_resp_forward.setEnabled(False)
        resp_bar.addWidget(self.btn_resp_forward)

        self.btn_resp_drop = SecondaryButton("✖ Drop Response")
        self.btn_resp_drop.clicked.connect(self._on_response_drop)
        self.btn_resp_drop.setEnabled(False)
        resp_bar.addWidget(self.btn_resp_drop)

        resp_layout.addLayout(resp_bar)

        self.response_edit = DarkEditor(
            placeholder="Intercepted response will appear here when Response Interception is enabled.",
            read_only=False,
        )
        self.response_edit.editor.setFont(QFont(FONT_MONO, 11))
        self.response_edit.editor.setMaximumHeight(200)
        self._hl_resp = HttpHighlighter(self.response_edit.editor.document())
        resp_layout.addWidget(self.response_edit)

        layout.addWidget(resp_widget)

        return widget

    # ─────────────────────────────────────────────────────────────────────────
    # HISTORY PANEL
    # ─────────────────────────────────────────────────────────────────────────

    def _build_history_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Toolbar
        tb = QHBoxLayout()
        tb.setSpacing(8)

        self.hist_search = QLineEdit()
        self.hist_search.setPlaceholderText("🔍 Filter (URL, method, status, notes…)")
        self.hist_search.textChanged.connect(self._apply_history_filter)
        self.hist_search.setMaximumWidth(360)
        self.hist_search.setStyleSheet(
            f"QLineEdit {{ background-color: {BACKGROUND}; color: {TEXT_PRIMARY}; "
            f"border: 1px solid {BORDER}; border-radius: {RADIUS_INPUT}px; padding: 4px 8px; font-size: 12px; }}"
        )
        tb.addWidget(self.hist_search)

        self.method_filter = QComboBox()
        self.method_filter.addItems(["All Methods", "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
        self.method_filter.currentTextChanged.connect(self._apply_history_filter)
        self.method_filter.setStyleSheet(
            f"QComboBox {{ background-color: {BACKGROUND}; color: {TEXT_PRIMARY}; "
            f"border: 1px solid {BORDER}; border-radius: {RADIUS_INPUT}px; padding: 4px 8px; min-width: 120px; }}"
        )
        tb.addWidget(self.method_filter)

        self.chk_scope_only = QCheckBox("Scope Only")
        self.chk_scope_only.setToolTip("Show only in-scope requests")
        self.chk_scope_only.stateChanged.connect(self._apply_history_filter)
        self.chk_scope_only.setStyleSheet(f"color: {TEXT_SECONDARY};")
        tb.addWidget(self.chk_scope_only)

        tb.addStretch()

        self.lbl_count = QLabel("0 requests")
        self.lbl_count.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        tb.addWidget(self.lbl_count)

        btn_export_json = SecondaryButton("⤓ JSON")
        btn_export_json.setToolTip("Export history session to JSON")
        btn_export_json.clicked.connect(self._export_json)
        btn_export_json.setMaximumWidth(80)
        tb.addWidget(btn_export_json)

        btn_import_json = SecondaryButton("⤒ JSON")
        btn_import_json.setToolTip("Import history session from JSON")
        btn_import_json.clicked.connect(self._import_json)
        btn_import_json.setMaximumWidth(80)
        tb.addWidget(btn_import_json)

        btn_clear = SecondaryButton("🗑 Clear")
        btn_clear.clicked.connect(self.clear_history)
        btn_clear.setMaximumWidth(80)
        tb.addWidget(btn_clear)

        layout.addLayout(tb)

        # Splitter: table + detail
        splitter = QSplitter(Qt.Vertical)

        # Request table
        self.hist_table = QTableWidget(0, 9)
        self.hist_table.setHorizontalHeaderLabels(
            ["#", "Method", "Host", "Path", "Status", "Length", "Time (ms)", "⚠", "Notes"]
        )
        self.hist_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.hist_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)
        self.hist_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        self.hist_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.hist_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.hist_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.hist_table.setAlternatingRowColors(True)
        self.hist_table.verticalHeader().setVisible(False)
        self.hist_table.setColumnWidth(0, 40)
        self.hist_table.setColumnWidth(1, 70)
        self.hist_table.setColumnWidth(2, 200)
        self.hist_table.setColumnWidth(4, 60)
        self.hist_table.setColumnWidth(5, 80)
        self.hist_table.setColumnWidth(6, 75)
        self.hist_table.setColumnWidth(7, 30)
        self.hist_table.currentCellChanged.connect(self._on_history_row_select)
        self.hist_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.hist_table.customContextMenuRequested.connect(self._on_history_table_menu)
        self.hist_table.doubleClicked.connect(self._on_history_double_click)
        self.hist_table.setStyleSheet(
            f"QTableWidget {{ background-color: {SURFACE}; color: {TEXT_SECONDARY}; "
            f"border: 1px solid {BORDER}; border-radius: {RADIUS_CARD}px; }}"
            f"QTableWidget::item {{ padding: 6px 10px; border: none; }}"
            f"QTableWidget::item:selected {{ background-color: {TEAL_PRIMARY}22; color: {TEXT_PRIMARY}; }}"
            f"QHeaderView::section {{ background-color: {BACKGROUND}; color: {TEXT_MUTED}; "
            f"border: none; border-bottom: 1px solid {BORDER}; padding: 6px 10px; "
            f"font-family: '{FONT_SANS}'; font-size: 11px; font-weight: 600; text-transform: uppercase; }}"
        )
        splitter.addWidget(self.hist_table)

        # Detail panel
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(4)

        btn_bar = QHBoxLayout()
        self.btn_repeater = SecondaryButton("↗ Send to Repeater")
        self.btn_repeater.clicked.connect(self._on_hist_to_repeater)
        self.btn_repeater.setEnabled(False)
        self.btn_intruder = SecondaryButton("⚡ Send to Intruder")
        self.btn_intruder.clicked.connect(self._on_hist_to_intruder)
        self.btn_intruder.setEnabled(False)
        btn_bar.addWidget(self.btn_repeater)
        btn_bar.addWidget(self.btn_intruder)
        btn_bar.addStretch()
        detail_layout.addLayout(btn_bar)

        detail_splitter = QSplitter(Qt.Horizontal)

        req_panel = QWidget()
        rq_layout = QVBoxLayout(req_panel)
        rq_layout.setContentsMargins(0, 0, 0, 0)
        rq_layout.setSpacing(2)
        rq_layout.addWidget(QLabel("REQUEST"))
        self.hist_req_view = QTextEdit()
        self.hist_req_view.setReadOnly(True)
        self.hist_req_view.setStyleSheet(
            f"QTextEdit {{ background-color: {BACKGROUND}; color: {TEXT_PRIMARY}; "
            f"border: 1px solid {BORDER}; border-radius: {RADIUS_INPUT}px; font-family: '{FONT_MONO}'; font-size: 11px; padding: 6px; }}"
        )
        font = QFont(FONT_MONO, 10)
        font.setStyleHint(QFont.Monospace)
        self.hist_req_view.setFont(font)
        rq_layout.addWidget(self.hist_req_view)
        detail_splitter.addWidget(req_panel)

        resp_panel = QWidget()
        rp_layout = QVBoxLayout(resp_panel)
        rp_layout.setContentsMargins(0, 0, 0, 0)
        rp_layout.setSpacing(2)
        rp_layout.addWidget(QLabel("RESPONSE"))
        self.hist_resp_view = QTextEdit()
        self.hist_resp_view.setReadOnly(True)
        self.hist_resp_view.setStyleSheet(
            f"QTextEdit {{ background-color: {BACKGROUND}; color: {TEXT_SECONDARY}; "
            f"border: 1px solid {BORDER}; border-radius: {RADIUS_INPUT}px; font-family: '{FONT_MONO}'; font-size: 11px; padding: 6px; }}"
        )
        self.hist_resp_view.setFont(font)
        rp_layout.addWidget(self.hist_resp_view)
        detail_splitter.addWidget(resp_panel)

        detail_layout.addWidget(detail_splitter)
        splitter.addWidget(detail_widget)
        splitter.setSizes([350, 300])
        layout.addWidget(splitter, stretch=1)

        return widget

    # ════════════════════════════════════════════════════════════════════════════
    # INTERCEPT LOGIC (original, preserved)
    # ═════════════════════════════════════════════════════════════════════════════

    def _raw_text_to_modifications(self) -> dict:
        text = self.request_edit.to_plain_text()
        lines = text.split("\n")
        mods = {}
        if not lines:
            return mods
        first = lines[0].strip().split()
        if len(first) >= 2:
            mods["method"] = first[0]
            mods["path"] = first[1]
        headers = {}
        body_start = None
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "":
                body_start = i + 1
                break
            if ":" in line:
                k, _, v = line.partition(":")
                headers[k.strip()] = v.strip()
        if headers:
            mods["headers"] = headers
        if body_start is not None:
            mods["body"] = "\n".join(lines[body_start:])
        return mods

    def _flow_to_raw(self, flow_data: dict) -> str:
        lines = []
        path = flow_data.get("path", "/")
        ver = flow_data.get("http_version", "HTTP/1.1")
        lines.append(f"{flow_data['method']} {path} {ver}")
        for k, v in flow_data.get("headers", {}).items():
            lines.append(f"{k}: {v}")
        lines.append("")
        body = flow_data.get("body", "")
        if body:
            lines.append(body)
        return "\n".join(lines)

    # ── Public API ──
    def show_intercepted(self, flow_data: dict):
        fid = flow_data["flow_id"]
        if fid in self._flows:
            return
        self._flows[fid] = flow_data
        self._order.append(fid)
        self._insert_row(flow_data, len(self._order))
        if self.table.currentRow() < 0:
            self.table.selectRow(0)

    def show_response(self, resp_data: dict):
        fid = resp_data["flow_id"]
        self._responses[fid] = resp_data
        # Update history row if visible
        for row in range(self.hist_table.rowCount()):
            item = self.hist_table.item(row, 0)
            if item and item.data(Qt.UserRole) == fid:
                code = resp_data.get("status_code", 0)
                color = get_severity_color("high") if code >= 500 else (
                    "#FBBF24" if code >= 400 else "#22D3EE" if code >= 300 else "#2DD4BF"
                )
                status_item = QTableWidgetItem(str(code))
                status_item.setForeground(QColor(color))
                status_item.setData(Qt.UserRole, fid)
                self.hist_table.setItem(row, 4, status_item)
                length_item = QTableWidgetItem(self._format_size(resp_data.get("length", 0)))
                length_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.hist_table.setItem(row, 5, length_item)
                time_item = QTableWidgetItem(f"{resp_data.get('elapsed_ms', 0):.1f}")
                time_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.hist_table.setItem(row, 6, time_item)
                break

    def show_response_intercept(self, event: dict):
        fid = event["flow_id"]
        self._current_resp_flow_id = fid
        raw = self._build_raw_response(event)
        self.response_edit.set_plain_text(raw)
        self.btn_resp_forward.setEnabled(True)
        self.btn_resp_drop.setEnabled(True)
        self.lbl_status.setText("⬤ Intercepted response waiting…")
        self.lbl_status.setStyleSheet(f"color: {CYAN_PRIMARY}; font-weight: 600;")

    def show_error(self, event: dict):
        fid = event.get("flow_id", "?")
        msg = event.get("message", "Unknown error")
        self.lbl_status.setText(f"⬤ Proxy error: {msg}")
        self.lbl_status.setStyleSheet(f"color: {DANGER}; font-weight: 600;")

    def _insert_row(self, flow_data: dict, idx: int):
        row = self.table.rowCount()
        self.table.insertRow(row)
        items = [
            (str(idx), Qt.AlignCenter, TEXT_MUTED),
            (flow_data.get("method", ""), Qt.AlignCenter, TEXT_PRIMARY),
            (flow_data.get("host", ""), Qt.AlignLeft, TEXT_SECONDARY),
            (flow_data.get("path", ""), Qt.AlignLeft, TEXT_PRIMARY),
        ]
        for col, (text, align, color) in enumerate(items):
            item = QTableWidgetItem(text)
            item.setTextAlignment(align | Qt.AlignVCenter)
            item.setForeground(QColor(color))
            item.setData(Qt.UserRole, flow_data["flow_id"])
            self.table.setItem(row, col, item)

    def _on_row_select(self, row, col, prev_row, prev_col):
        item = self.table.item(row, 0)
        if not item:
            return
        fid = item.data(Qt.UserRole)
        if fid is None or fid not in self._flows:
            return
        self._current_flow_id = fid
        flow = self._flows[fid]
        raw = self._flow_to_raw(flow)
        self.request_edit.set_plain_text(raw)
        self.btn_forward.setEnabled(True)
        self.btn_drop.setEnabled(True)
        self.btn_to_repeater.setEnabled(True)
        self.btn_to_intruder.setEnabled(True)

        # Metadata
        meta = (
            f"Flow ID : {fid}\n"
            f"Method  : {flow.get('method', '')}\n"
            f"URL     : {flow.get('url', '')}\n"
            f"Host    : {flow.get('host', '')}:{flow.get('port', '')}\n"
            f"Scheme  : {flow.get('scheme', '')}\n"
            f"Time    : {flow.get('timestamp', '')}\n"
        )
        self.info_view.setPlainText(meta)

        # Sensitive data scan
        matches = scan_text(raw)
        if matches:
            self.lbl_sensitive.setText(f"⚠ {len(matches)} sensitive item(s) detected")
            self.lbl_sensitive.setVisible(True)
        else:
            self.lbl_sensitive.setVisible(False)

    def _remove_current_flow(self):
        if not self._current_flow_id:
            return
        fid = self._current_flow_id
        self._flows.pop(fid, None)
        self._order = [x for x in self._order if x != fid]
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == fid:
                self.table.removeRow(row)
                break
        self._current_flow_id = None
        self.request_edit.set_plain_text("")
        self.info_view.clear()
        self.btn_forward.setEnabled(False)
        self.btn_drop.setEnabled(False)
        self.btn_to_repeater.setEnabled(False)
        self.btn_to_intruder.setEnabled(False)
        self.lbl_sensitive.setVisible(False)

    # ── Slots ──
    def _on_forward(self):
        if not self._current_flow_id:
            return
        mods = self._raw_text_to_modifications()
        self.proxy.forward_flow(self._current_flow_id, mods)
        self._remove_current_flow()

    def _on_drop(self):
        if not self._current_flow_id:
            return
        self.proxy.drop_flow(self._current_flow_id)
        self._remove_current_flow()

    def _on_forward_all(self):
        for fid in list(self._flows.keys()):
            self.proxy.forward_flow(fid)
        self.table.setRowCount(0)
        self._flows.clear()
        self._order.clear()
        self._current_flow_id = None
        self.request_edit.set_plain_text("")
        self.info_view.clear()
        self.btn_forward.setEnabled(False)
        self.btn_drop.setEnabled(False)
        self.btn_forward_all.setEnabled(False)
        self.btn_drop_all.setEnabled(False)
        self.btn_to_repeater.setEnabled(False)
        self.btn_to_intruder.setEnabled(False)
        self.lbl_sensitive.setVisible(False)

    def _on_drop_all(self):
        if self._confirm_drop_all:
            reply = QMessageBox.question(
                self, "Drop All",
                "Drop all pending intercepted requests?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        for fid in list(self._flows.keys()):
            self.proxy.drop_flow(fid)
        self.table.setRowCount(0)
        self._flows.clear()
        self._order.clear()
        self._current_flow_id = None
        self.request_edit.set_plain_text("")
        self.info_view.clear()
        self.btn_forward.setEnabled(False)
        self.btn_drop.setEnabled(False)
        self.btn_forward_all.setEnabled(False)
        self.btn_drop_all.setEnabled(False)
        self.btn_to_repeater.setEnabled(False)
        self.btn_to_intruder.setEnabled(False)
        self.lbl_sensitive.setVisible(False)

    def _on_response_forward(self):
        if not self._current_resp_flow_id:
            return
        mods = {}
        text = self.response_edit.to_plain_text()
        lines = text.split("\n")
        if lines:
            first = lines[0].strip().split()
            if len(first) >= 2:
                try:
                    mods["status_code"] = int(first[1])
                except ValueError:
                    pass
        headers = {}
        body_start = None
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "":
                body_start = i + 1
                break
            if ":" in line:
                k, _, v = line.partition(":")
                headers[k.strip()] = v.strip()
        if headers:
            mods["headers"] = headers
        if body_start is not None:
            mods["body"] = "\n".join(lines[body_start:])
        self.proxy.forward_flow(self._current_resp_flow_id, mods)
        self.btn_resp_forward.setEnabled(False)
        self.btn_resp_drop.setEnabled(False)
        self.response_edit.set_plain_text("")
        self._current_resp_flow_id = None
        self.lbl_status.setText("⬤ Waiting for intercepted request…")
        self.lbl_status.setStyleSheet(f"color: {TEAL_PRIMARY}; font-weight: 600;")

    def _on_response_drop(self):
        if not self._current_resp_flow_id:
            return
        self.proxy.drop_flow(self._current_resp_flow_id)
        self.btn_resp_forward.setEnabled(False)
        self.btn_resp_drop.setEnabled(False)
        self.response_edit.set_plain_text("")
        self._current_resp_flow_id = None
        self.lbl_status.setText("⬤ Waiting for intercepted request…")
        self.lbl_status.setStyleSheet(f"color: {TEAL_PRIMARY}; font-weight: 600;")

    def _on_send_to_repeater(self):
        if not self._current_flow_id:
            return
        flow = self._flows[self._current_flow_id]
        raw = self.request_edit.to_plain_text()
        host_port = (flow.get("host", "127.0.0.1"), flow.get("port", 80))
        self.send_to_repeater.emit(raw, host_port)

    def _on_send_to_intruder(self):
        if not self._current_flow_id:
            return
        raw = self.request_edit.to_plain_text()
        self.send_to_intruder.emit(raw)

    def _apply_filter(self):
        text = self.search_box.text().lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if not item:
                continue
            visible = False
            for col in range(1, 4):
                cell = self.table.item(row, col)
                if cell and text in cell.text().lower():
                    visible = True
                    break
            self.table.setRowHidden(row, not visible)

    def _on_table_menu(self, pos):
        menu = QMenu(self)
        act_fwd = QAction("Forward", self)
        act_fwd.triggered.connect(self._on_forward)
        act_drop = QAction("Drop", self)
        act_drop.triggered.connect(self._on_drop)
        act_rep = QAction("Send to Repeater", self)
        act_rep.triggered.connect(self._on_send_to_repeater)
        act_int = QAction("Send to Intruder", self)
        act_int.triggered.connect(self._on_send_to_intruder)
        menu.addAction(act_fwd)
        menu.addAction(act_drop)
        menu.addSeparator()
        menu.addAction(act_rep)
        menu.addAction(act_int)
        menu.exec_(self.table.mapToGlobal(pos))

    # ════════════════════════════════════════════════════════════════════════════
    # HISTORY LOGIC (original, preserved)
    # ═════════════════════════════════════════════════════════════════════════════

    def add_request(self, flow_data: dict):
        fid = flow_data["flow_id"]
        if fid in self._flows:
            return
        self._flows[fid] = flow_data
        self._order.append(fid)
        self._insert_history_row(flow_data, len(self._order))

    def update_response(self, resp_data: dict):
        fid = resp_data["flow_id"]
        self._responses[fid] = resp_data
        for row in range(self.hist_table.rowCount()):
            item = self.hist_table.item(row, 0)
            if item and item.data(Qt.UserRole) == fid:
                code = resp_data.get("status_code", 0)
                color = get_severity_color("high") if code >= 500 else (
                    "#FBBF24" if code >= 400 else "#22D3EE" if code >= 300 else "#2DD4BF"
                )
                status_item = QTableWidgetItem(str(code))
                status_item.setForeground(QColor(color))
                status_item.setData(Qt.UserRole, fid)
                self.hist_table.setItem(row, 4, status_item)
                length_item = QTableWidgetItem(self._format_size(resp_data.get("length", 0)))
                length_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.hist_table.setItem(row, 5, length_item)
                time_item = QTableWidgetItem(f"{resp_data.get('elapsed_ms', 0):.1f}")
                time_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.hist_table.setItem(row, 6, time_item)
                break
        self.lbl_count.setText(f"{len(self._order)} requests")

    def clear_history(self):
        self._flows.clear()
        self._responses.clear()
        self._order.clear()
        self.hist_table.setRowCount(0)
        self.hist_req_view.clear()
        self.hist_resp_view.clear()
        self.btn_repeater.setEnabled(False)
        self.btn_intruder.setEnabled(False)
        self.lbl_count.setText("0 requests")

    def get_flows(self) -> dict:
        return dict(self._flows)

    def get_responses(self) -> dict:
        return dict(self._responses)

    def get_notes(self) -> dict:
        return dict(self._notes)

    def set_notes(self, notes: dict):
        self._notes = dict(notes)
        for row in range(self.hist_table.rowCount()):
            item = self.hist_table.item(row, 0)
            if item:
                fid = item.data(Qt.UserRole)
                note = self._notes.get(fid, "")
                notes_item = self.hist_table.item(row, 8)
                if notes_item:
                    notes_item.setText(note)

    def load_session_data(self, data: dict):
        # flows and responses restored by MainWindow
        pass

    # ── Private helpers ──
    def _insert_history_row(self, flow_data: dict, idx: int):
        row = self.hist_table.rowCount()
        self.hist_table.insertRow(row)
        code = ""
        color = TEXT_MUTED
        items = [
            (str(idx), Qt.AlignCenter, TEXT_MUTED),
            (flow_data.get("method", ""), Qt.AlignCenter, TEXT_PRIMARY),
            (flow_data.get("host", ""), Qt.AlignLeft, TEXT_SECONDARY),
            (flow_data.get("path", ""), Qt.AlignLeft, TEXT_PRIMARY),
            (code, Qt.AlignCenter, color),
            ("", Qt.AlignRight | Qt.AlignVCenter, TEXT_SECONDARY),
            ("", Qt.AlignRight | Qt.AlignVCenter, TEXT_SECONDARY),
            ("", Qt.AlignCenter, TEXT_MUTED),
            ("", Qt.AlignLeft, TEXT_SECONDARY),
        ]
        for col, (text, align, color) in enumerate(items):
            item = QTableWidgetItem(text)
            item.setTextAlignment(align | Qt.AlignVCenter)
            item.setForeground(QColor(color))
            item.setData(Qt.UserRole, flow_data["flow_id"])
            self.hist_table.setItem(row, col, item)

    def _on_history_row_select(self, row, col, prev_row, prev_col):
        item = self.hist_table.item(row, 0)
        if not item:
            return
        fid = item.data(Qt.UserRole)
        if fid is None or fid not in self._flows:
            return
        flow = self._flows[fid]
        self.hist_req_view.setPlainText(self._flow_to_raw(flow))
        resp = self._responses.get(fid)
        if resp:
            self.hist_resp_view.setPlainText(self._build_raw_response(resp))
        else:
            self.hist_resp_view.clear()
        self.btn_repeater.setEnabled(True)
        self.btn_intruder.setEnabled(True)

    def _on_history_double_click(self):
        self._on_hist_to_repeater()

    def _on_hist_to_repeater(self):
        item = self.hist_table.currentItem()
        if not item:
            return
        row = item.row()
        fid_item = self.hist_table.item(row, 0)
        if not fid_item:
            return
        fid = fid_item.data(Qt.UserRole)
        flow = self._flows.get(fid)
        if not flow:
            return
        raw = self.hist_req_view.toPlainText()
        host_port = (flow.get("host", "127.0.0.1"), flow.get("port", 80))
        self.send_to_repeater.emit(raw, host_port)

    def _on_hist_to_intruder(self):
        raw = self.hist_req_view.toPlainText()
        if raw:
            self.send_to_intruder.emit(raw)

    def _apply_history_filter(self):
        text = self.hist_search.text().lower()
        method = self.method_filter.currentText()
        for row in range(self.hist_table.rowCount()):
            visible = True
            if method != "All Methods":
                method_item = self.hist_table.item(row, 1)
                if method_item and method_item.text() != method:
                    visible = False
            if text and visible:
                match = False
                for col in range(2, 9):
                    cell = self.hist_table.item(row, col)
                    if cell and text in cell.text().lower():
                        match = True
                        break
                visible = match
            self.hist_table.setRowHidden(row, not visible)

    def _on_history_table_menu(self, pos):
        menu = QMenu(self)
        act_rep = QAction("Send to Repeater", self)
        act_rep.triggered.connect(self._on_hist_to_repeater)
        act_int = QAction("Send to Intruder", self)
        act_int.triggered.connect(self._on_hist_to_intruder)
        menu.addAction(act_rep)
        menu.addAction(act_int)
        menu.exec_(self.hist_table.mapToGlobal(pos))

    def _format_size(self, n: int) -> str:
        if n < 1024:
            return f"{n} B"
        if n < 1024 * 1024:
            return f"{n / 1024:.1f} KB"
        return f"{n / (1024 * 1024):.1f} MB"

    def _build_raw_request(self, flow: dict) -> str:
        return self._flow_to_raw(flow)

    def _build_raw_response(self, resp: dict) -> str:
        lines = []
        lines.append(f"HTTP/1.1 {resp.get('status_code', 0)} {resp.get('reason', '')}")
        for k, v in resp.get("headers", {}).items():
            lines.append(f"{k}: {v}")
        lines.append("")
        body = resp.get("body", "")
        if body:
            lines.append(body)
        return "\n".join(lines)

    # ── Export / Import ──
    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export History", "history_session.json", "JSON Files (*.json)"
        )
        if not path:
            return
        import json
        data = []
        for fid in self._order:
            flow = self._flows.get(fid, {})
            resp = self._responses.get(fid, {})
            data.append({"flow": flow, "response": resp})
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=True)
        except Exception:
            pass

    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import History", "", "JSON Files (*.json)"
        )
        if not path:
            return
        import json
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return
        if not isinstance(data, list):
            return
        self.clear_history()
        for idx, entry in enumerate(data, start=1):
            flow = entry.get("flow") if isinstance(entry, dict) else None
            resp = entry.get("response") if isinstance(entry, dict) else None
            if not isinstance(flow, dict):
                continue
            flow.setdefault("flow_id", f"import-{idx}")
            self.add_request(flow)
            if isinstance(resp, dict) and resp:
                resp["flow_id"] = flow["flow_id"]
                self.update_response(resp)