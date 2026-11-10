"""
EXVOLT — History Page
Premium HTTP history interface with search, filters, request/response details.
All original HistoryTab functionality and callbacks are preserved.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableWidget, QTableWidgetItem,
    QTextEdit, QLabel, QPushButton, QHeaderView, QLineEdit, QComboBox,
    QAbstractItemView, QFileDialog, QMenu, QAction, QApplication, QCheckBox,
)
import json
import csv
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from .design_tokens import (
    BACKGROUND, SURFACE, SURFACE_ELEVATED, TEAL_PRIMARY, CYAN_PRIMARY,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER, BORDER_TEAL,
    SUCCESS, DANGER, INFO, FONT_SANS, FONT_MONO,
    RADIUS_CARD, RADIUS_INPUT,
)
from ..components import (
    GlassCard, SectionHeader, StatusBadge, PrimaryButton, SecondaryButton,
    IconButton, Toolbar, DarkTable, DarkEditor, EmptyState,
)
from core.sensitive_patterns import has_sensitive_data


class HistoryPage(QWidget):
    """
    HTTP History page.
    Signals:
        send_to_repeater(str, tuple)  # (raw_request, (host, port))
        send_to_intruder(str)          # raw_request
    """

    send_to_repeater = pyqtSignal(str, tuple)
    send_to_intruder = pyqtSignal(str)

    def __init__(self, proxy, scope_manager, parent=None):
        super().__init__(parent)
        self.proxy = proxy
        self.scope_manager = scope_manager

        self._flows: dict = {}
        self._responses: dict = {}
        self._notes: dict = {}
        self._order: list = []

        self._setup_ui()

    # ════════════════════════════════════════════════════════════════════════════
    # UI
    # ════════════════════════════════════════════════════════════════════════════

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Toolbar ──
        tb = QHBoxLayout()
        tb.setSpacing(8)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Filter (URL, method, status, notes…)")
        self.search_box.textChanged.connect(self._apply_filter)
        self.search_box.setMaximumWidth(360)
        self.search_box.setStyleSheet(
            f"QLineEdit {{ background-color: {BACKGROUND}; color: {TEXT_PRIMARY}; "
            f"border: 1px solid {BORDER}; border-radius: 6px; padding: 4px 8px; font-size: 12px; }}"
        )
        tb.addWidget(self.search_box)

        self.method_filter = QComboBox()
        self.method_filter.addItems(["All Methods", "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
        self.method_filter.currentTextChanged.connect(self._apply_filter)
        self.method_filter.setStyleSheet(
            f"QComboBox {{ background-color: {BACKGROUND}; color: {TEXT_PRIMARY}; "
            f"border: 1px solid {BORDER}; border-radius: 6px; padding: 4px 8px; min-width: 120px; }}"
        )
        tb.addWidget(self.method_filter)

        self.chk_scope_only = QCheckBox("Scope Only")
        self.chk_scope_only.setToolTip("Show only in-scope requests")
        self.chk_scope_only.stateChanged.connect(self._apply_filter)
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

        btn_export_csv = SecondaryButton("⤓ CSV")
        btn_export_csv.setToolTip("Export history session to CSV")
        btn_export_csv.clicked.connect(self._export_csv)
        btn_export_csv.setMaximumWidth(80)
        tb.addWidget(btn_export_csv)

        btn_import_csv = SecondaryButton("⤒ CSV")
        btn_import_csv.setToolTip("Import history session from CSV")
        btn_import_csv.clicked.connect(self._import_csv)
        btn_import_csv.setMaximumWidth(80)
        tb.addWidget(btn_import_csv)

        btn_clear = SecondaryButton("🗑 Clear")
        btn_clear.clicked.connect(self.clear_history)
        btn_clear.setMaximumWidth(80)
        tb.addWidget(btn_clear)

        layout.addLayout(tb)

        # ── Splitter: table + detail ──
        splitter = QSplitter(Qt.Vertical)

        # Request table
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["#", "Method", "Host", "Path", "Status", "Length", "Time (ms)", "⚠", "Notes"]
        )
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 75)
        self.table.setColumnWidth(7, 30)
        self.table.currentCellChanged.connect(self._on_row_select)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_table_menu)
        self.table.doubleClicked.connect(self._on_double_click)
        self.table.setStyleSheet(
            f"QTableWidget {{ background-color: {SURFACE}; color: {TEXT_SECONDARY}; "
            f"border: 1px solid {BORDER}; border-radius: 12px; }}"
            f"QTableWidget::item {{ padding: 6px 10px; border: none; }}"
            f"QTableWidget::item:selected {{ background-color: {TEAL_PRIMARY}22; color: {TEXT_PRIMARY}; }}"
            f"QHeaderView::section {{ background-color: {BACKGROUND}; color: {TEXT_MUTED}; "
            f"border: none; border-bottom: 1px solid {BORDER}; padding: 6px 10px; "
            f"font-family: '{FONT_SANS}'; font-size: 11px; font-weight: 600; text-transform: uppercase; }}"
        )
        splitter.addWidget(self.table)

        # Detail panel
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(4)

        btn_bar = QHBoxLayout()
        self.btn_repeater = SecondaryButton("↗ Send to Repeater")
        self.btn_repeater.clicked.connect(self._on_to_repeater)
        self.btn_repeater.setEnabled(False)
        self.btn_intruder = SecondaryButton("⚡ Send to Intruder")
        self.btn_intruder.clicked.connect(self._on_to_intruder)
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
        self.req_view = QTextEdit()
        self.req_view.setReadOnly(True)
        self.req_view.setStyleSheet(
            f"QTextEdit {{ background-color: {BACKGROUND}; color: {TEXT_PRIMARY}; "
            f"border: 1px solid {BORDER}; border-radius: 6px; font-family: '{FONT_MONO}'; font-size: 11px; padding: 6px; }}"
        )
        font = QFont(FONT_MONO, 10)
        font.setStyleHint(QFont.Monospace)
        self.req_view.setFont(font)
        rq_layout.addWidget(self.req_view)
        detail_splitter.addWidget(req_panel)

        resp_panel = QWidget()
        rp_layout = QVBoxLayout(resp_panel)
        rp_layout.setContentsMargins(0, 0, 0, 0)
        rp_layout.setSpacing(2)
        rp_layout.addWidget(QLabel("RESPONSE"))
        self.resp_view = QTextEdit()
        self.resp_view.setReadOnly(True)
        self.resp_view.setStyleSheet(
            f"QTextEdit {{ background-color: {BACKGROUND}; color: {TEXT_SECONDARY}; "
            f"border: 1px solid {BORDER}; border-radius: 6px; font-family: '{FONT_MONO}'; font-size: 11px; padding: 6px; }}"
        )
        self.resp_view.setFont(font)
        rp_layout.addWidget(self.resp_view)
        detail_splitter.addWidget(resp_panel)

        detail_layout.addWidget(detail_splitter)
        splitter.addWidget(detail_widget)
        splitter.setSizes([350, 300])
        layout.addWidget(splitter, stretch=1)

    # ════════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ════════════════════════════════════════════════════════════════════════════

    def add_request(self, flow_data: dict):
        fid = flow_data["flow_id"]
        if fid in self._flows:
            return
        self._flows[fid] = flow_data
        self._order.append(fid)
        self._insert_row(flow_data, len(self._order))

    def update_response(self, resp_data: dict):
        fid = resp_data["flow_id"]
        self._responses[fid] = resp_data
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == fid:
                code = resp_data.get("status_code", 0)
                color = self._status_color(code)
                status_item = QTableWidgetItem(str(code))
                status_item.setForeground(QColor(color))
                status_item.setData(Qt.UserRole, fid)
                self.table.setItem(row, 4, status_item)
                length_item = QTableWidgetItem(self._format_size(resp_data.get("length", 0)))
                length_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, 5, length_item)
                time_item = QTableWidgetItem(f"{resp_data.get('elapsed_ms', 0):.1f}")
                time_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, 6, time_item)
                break
        self.lbl_count.setText(f"{len(self._order)} requests")

    def clear_history(self):
        self._flows.clear()
        self._responses.clear()
        self._order.clear()
        self.table.setRowCount(0)
        self.req_view.clear()
        self.resp_view.clear()
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
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                fid = item.data(Qt.UserRole)
                note = self._notes.get(fid, "")
                notes_item = self.table.item(row, 8)
                if notes_item:
                    notes_item.setText(note)

    def load_session_data(self, data: dict):
        pass

    # ════════════════════════════════════════════════════════════════════════════
    # PRIVATE
    # ════════════════════════════════════════════════════════════════════════════

    def _status_color(self, code: int) -> str:
        if 200 <= code < 300:
            return "#2DD4BF"
        if 300 <= code < 400:
            return "#22D3EE"
        if 400 <= code < 500:
            return "#FBBF24"
        if 500 <= code < 600:
            return "#FB7185"
        return "#647477"

    def _format_size(self, n: int) -> str:
        if n < 1024:
            return f"{n} B"
        if n < 1024 * 1024:
            return f"{n / 1024:.1f} KB"
        return f"{n / (1024 * 1024):.1f} MB"

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

    def _insert_row(self, flow_data: dict, idx: int):
        row = self.table.rowCount()
        self.table.insertRow(row)
        items = [
            (str(idx), Qt.AlignCenter, TEXT_MUTED),
            (flow_data.get("method", ""), Qt.AlignCenter, TEXT_PRIMARY),
            (flow_data.get("host", ""), Qt.AlignLeft, TEXT_SECONDARY),
            (flow_data.get("path", ""), Qt.AlignLeft, TEXT_PRIMARY),
            ("", Qt.AlignCenter, TEXT_MUTED),
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
            self.table.setItem(row, col, item)

    def _on_row_select(self, row, col, prev_row, prev_col):
        item = self.table.item(row, 0)
        if not item:
            return
        fid = item.data(Qt.UserRole)
        if fid is None or fid not in self._flows:
            return
        flow = self._flows[fid]
        self.req_view.setPlainText(self._flow_to_raw(flow))
        resp = self._responses.get(fid)
        if resp:
            self.resp_view.setPlainText(self._build_raw_response(resp))
        else:
            self.resp_view.clear()
        self.btn_repeater.setEnabled(True)
        self.btn_intruder.setEnabled(True)

    def _on_double_click(self):
        self._on_to_repeater()

    def _on_to_repeater(self):
        item = self.table.currentItem()
        if not item:
            return
        row = item.row()
        fid_item = self.table.item(row, 0)
        if not fid_item:
            return
        fid = fid_item.data(Qt.UserRole)
        flow = self._flows.get(fid)
        if not flow:
            return
        raw = self.req_view.toPlainText()
        host_port = (flow.get("host", "127.0.0.1"), flow.get("port", 80))
        self.send_to_repeater.emit(raw, host_port)

    def _on_to_intruder(self):
        raw = self.req_view.toPlainText()
        if raw:
            self.send_to_intruder.emit(raw)

    def _apply_filter(self):
        text = self.search_box.text().lower()
        method = self.method_filter.currentText()
        for row in range(self.table.rowCount()):
            visible = True
            if method != "All Methods":
                method_item = self.table.item(row, 1)
                if method_item and method_item.text() != method:
                    visible = False
            if text and visible:
                match = False
                for col in range(2, 9):
                    cell = self.table.item(row, col)
                    if cell and text in cell.text().lower():
                        match = True
                        break
                visible = match
            self.table.setRowHidden(row, not visible)

    def _on_table_menu(self, pos):
        menu = QMenu(self)
        act_rep = QAction("Send to Repeater", self)
        act_rep.triggered.connect(self._on_to_repeater)
        act_int = QAction("Send to Intruder", self)
        act_int.triggered.connect(self._on_to_intruder)
        menu.addAction(act_rep)
        menu.addAction(act_int)
        menu.exec_(self.table.mapToGlobal(pos))

    # ── Export / Import ──
    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export History", "history_session.json", "JSON Files (*.json)"
        )
        if not path:
            return
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

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export History", "history_session.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        fields = ["method", "url", "host", "path", "status", "length", "time_ms", "raw_request", "raw_response"]
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                for fid in self._order:
                    flow = self._flows.get(fid, {})
                    resp = self._responses.get(fid, {})
                    raw_req = self._flow_to_raw(flow)
                    raw_resp = self._build_raw_response(resp)
                    writer.writerow({
                        "method": flow.get("method", ""),
                        "url": flow.get("url", ""),
                        "host": flow.get("host", ""),
                        "path": flow.get("path", ""),
                        "status": resp.get("status_code", ""),
                        "length": resp.get("length", ""),
                        "time_ms": resp.get("elapsed_ms", ""),
                        "raw_request": raw_req,
                        "raw_response": raw_resp,
                    })
        except Exception:
            pass

    def _import_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import History", "", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.clear_history()
                for idx, row in enumerate(reader, start=1):
                    flow = {
                        "flow_id": f"import-{idx}",
                        "method": row.get("method", ""),
                        "url": row.get("url", ""),
                        "host": row.get("host", ""),
                        "path": row.get("path", ""),
                        "headers": {},
                        "body": row.get("raw_request", ""),
                        "timestamp": "",
                    }
                    resp = {
                        "flow_id": flow["flow_id"],
                        "status_code": int(row.get("status", 0) or 0),
                        "reason": "",
                        "headers": {},
                        "body": row.get("raw_response", ""),
                        "elapsed_ms": float(row.get("time_ms", 0) or 0),
                        "length": int(row.get("length", 0) or 0),
                    }
                    self.add_request(flow)
                    self.update_response(resp)
        except Exception:
            pass