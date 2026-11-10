"""
Vers Suite - Intruder Tab
Automated payload injection (OWASP Top 10 categories).
Modes: Sniper | Battering Ram | Cluster Bomb
"""

import os
import re
import time
import socket
import ssl
import threading
import json
import csv
from typing import List, Tuple, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QTextEdit, QLabel, QLineEdit, QSpinBox,
    QComboBox, QCheckBox, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QProgressBar, QAbstractItemView,
    QGroupBox, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QFont, QTextCursor, QTextCharFormat
from .styles import status_color, COLORS
from .intercept_tab import HttpHighlighter
import itertools


PAYLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "payloads")


# ─────────────────────────────────────────────
# Attack Worker
# ─────────────────────────────────────────────
class AttackWorker(QObject):
    result  = pyqtSignal(int, str, int, int, float)  # (idx, payload_str, status, length, ms)
    progress = pyqtSignal(int, int)                   # (done, total)
    finished = pyqtSignal()
    stopped  = pyqtSignal()

    def __init__(self, host, port, raw_template, mode, payload_sets, use_ssl, concurrency=5, timeout=10):
        super().__init__()
        self.host        = host
        self.port        = port
        self.raw_template = raw_template
        self.mode        = mode             # "Sniper", "Battering Ram", "Cluster Bomb"
        self.payload_sets = payload_sets    # dict of {set_idx (int): list of payloads}
        self.use_ssl     = use_ssl
        self.concurrency = concurrency
        self.timeout     = timeout
        self._stop       = False

    def stop(self):
        self._stop = True

    def run(self):
        lock  = threading.Lock()
        done  = [0]
        threads = []
        tasks = []

        # Find markers
        marker_count = self.raw_template.count("§") // 2
        if marker_count == 0:
            marker_count = 1

        # Build task list depending on mode
        if self.mode == "Sniper":
            set1 = self.payload_sets.get(1, [])
            for m_idx in range(marker_count):
                for p in set1:
                    tasks.append((m_idx, [p]))

        elif self.mode == "Battering Ram":
            set1 = self.payload_sets.get(1, [])
            for p in set1:
                tasks.append((None, [p] * marker_count))

        elif self.mode == "Cluster Bomb":
            lists = [self.payload_sets.get(i + 1, []) for i in range(marker_count)]
            # If a list is empty for a marker, use a default empty string so product doesn't yield nothing
            lists = [l if l else [""] for l in lists]
            for combo in itertools.product(*lists):
                tasks.append((None, list(combo)))

        total = len(tasks)
        if total == 0:
            self.finished.emit()
            return

        sema  = threading.Semaphore(self.concurrency)

        for idx, (m_idx, p_list) in enumerate(tasks):
            if self._stop:
                self.stopped.emit()
                return

            def task(i=idx, m=m_idx, pl=p_list):
                sema.acquire()
                try:
                    if self._stop:
                        return
                    status, length, ms = self._send_one(m, pl)
                    p_str = " | ".join(pl)
                    self.result.emit(i, p_str[:100], status, length, ms)
                    with lock:
                        done[0] += 1
                        self.progress.emit(done[0], total)
                finally:
                    sema.release()

            t = threading.Thread(target=task, daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        if not self._stop:
            self.finished.emit()

    def _send_one(self, target_marker_idx: Optional[int], mapped_payloads: List[str]) -> Tuple[int, int, float]:
        try:
            # Reconstruct request by replacing markers
            parts = self.raw_template.split("§")
            if len(parts) % 2 == 0:
                parts.append("") # Malformed markers, fallback

            raw = ""
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    raw += part
                else:
                    marker_idx = i // 2
                    if target_marker_idx is not None:
                        # Sniper mode: only inject one marker, clear others
                        if marker_idx == target_marker_idx:
                            raw += mapped_payloads[0]
                    else:
                        # Battering Ram / Cluster Bomb: inject mapped payload
                        if marker_idx < len(mapped_payloads):
                            raw += mapped_payloads[marker_idx]

            raw = raw.replace("\r\n", "\n").replace("\n", "\r\n")
            if not raw.endswith("\r\n\r\n"):
                raw += "\r\n\r\n"

            t0   = time.time()
            sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            if self.use_ssl:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode    = ssl.CERT_NONE
                sock = ctx.wrap_socket(sock, server_hostname=self.host)

            sock.sendall(raw.encode("utf-8", errors="replace"))

            chunks = []
            while True:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                chunks.append(chunk)
            sock.close()

            elapsed = (time.time() - t0) * 1000
            resp_raw = b"".join(chunks)
            status = 0
            first_line = resp_raw.split(b"\r\n")[0].decode("utf-8", errors="replace")
            resp_parts = first_line.split()
            if len(resp_parts) >= 2:
                try:
                    status = int(resp_parts[1])
                except ValueError:
                    pass
            return status, len(resp_raw), round(elapsed, 1)

        except Exception:
            return 0, 0, 0.0

# ─────────────────────────────────────────────
# Intruder Tab
# ─────────────────────────────────────────────
class IntruderTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker  = None
        self._thread  = None
        self._results: list = []
        self._payload_sets: dict = {i: "" for i in range(1, 11)} # up to 10 sets
        self._current_set = 1
        self._setup_ui()
        self._load_payload_list()

    def _setup_ui(self):
        from PyQt5.QtWidgets import (
            QVBoxLayout, QHBoxLayout, QFrame, QSplitter, QScrollArea,
            QGroupBox, QLabel, QPushButton, QTextEdit, QLineEdit,
            QSpinBox, QComboBox, QCheckBox, QProgressBar,
            QTableWidget, QHeaderView, QAbstractItemView, QWidget
        )
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        def panel(title, subtitle=None):
            box = QFrame()
            box.setObjectName("exvoltPanel")
            box.setStyleSheet(
                "QFrame#exvoltPanel{background:#11171d;"
                "border:1px solid #26313a;border-radius:10px;}"
            )
            lay = QVBoxLayout(box)
            lay.setContentsMargins(14, 12, 14, 14)
            lay.setSpacing(9)
            head = QHBoxLayout()
            name = QLabel(title)
            name.setStyleSheet("font-size:13px;font-weight:700;color:#e6edf3;")
            head.addWidget(name)
            head.addStretch()
            if subtitle:
                sub = QLabel(subtitle)
                sub.setStyleSheet("color:#84919d;font-size:10px;")
                head.addWidget(sub)
            lay.addLayout(head)
            return box, lay

        # Workspace header
        header = QHBoxLayout()
        titlebox = QVBoxLayout()
        title = QLabel("Intruder")
        title.setStyleSheet("font-size:22px;font-weight:750;color:#e6edf3;")
        desc = QLabel("Payload-driven request testing")
        desc.setStyleSheet("color:#84919d;font-size:11px;")
        titlebox.addWidget(title)
        titlebox.addWidget(desc)
        header.addLayout(titlebox)
        header.addStretch()

        self.btn_attack = QPushButton("Run attack")
        self.btn_attack.setObjectName("btn_attack")
        self.btn_attack.setMinimumHeight(34)
        self.btn_attack.clicked.connect(self._on_attack)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("btn_drop")
        self.btn_stop.setMinimumHeight(34)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop)
        header.addWidget(self.btn_stop)
        header.addWidget(self.btn_attack)
        root.addLayout(header)

        # Main work area
        main = QSplitter(Qt.Horizontal)
        main.setChildrenCollapsible(False)

        request_panel, rq = panel("Request template", "HTTP")
        self.request_edit = QTextEdit()
        self.request_edit.setObjectName("raw_request")
        self.request_edit.setPlaceholderText(
            "Paste HTTP request. Mark injection points with §...§\n\n"
            "POST /login HTTP/1.1\nHost: target.example\n\nuser=§admin§"
        )
        font = QFont("Cascadia Code", 10)
        font.setStyleHint(QFont.Monospace)
        self.request_edit.setFont(font)
        self._hl = HttpHighlighter(self.request_edit.document())
        rq.addWidget(self.request_edit, 1)

        markerbar = QHBoxLayout()
        marker_add = QPushButton("Add § marker")
        marker_add.clicked.connect(self._add_marker)
        marker_clear = QPushButton("Clear markers")
        marker_clear.clicked.connect(self._clear_markers)
        markerbar.addWidget(marker_add)
        markerbar.addWidget(marker_clear)
        markerbar.addStretch()
        rq.addLayout(markerbar)
        main.addWidget(request_panel)

        # Right inspector
        inspector = QWidget()
        il = QVBoxLayout(inspector)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(10)

        target, tl = panel("Target")
        row = QHBoxLayout()
        self.host_input = QLineEdit("127.0.0.1")
        self.host_input.setPlaceholderText("Hostname")
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(80)
        self.ssl_check = QCheckBox("TLS")
        row.addWidget(self.host_input, 1)
        row.addWidget(self.port_input)
        row.addWidget(self.ssl_check)
        tl.addLayout(row)
        il.addWidget(target)

        config, cl = panel("Attack configuration")
        row = QHBoxLayout()
        row.addWidget(QLabel("Mode"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Sniper", "Battering Ram", "Cluster Bomb"])
        row.addWidget(self.mode_combo, 1)
        cl.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(QLabel("Threads"))
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 50)
        self.threads_spin.setValue(10)
        row.addWidget(self.threads_spin)
        row.addWidget(QLabel("Timeout"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(10)
        self.timeout_spin.setSuffix(" s")
        row.addWidget(self.timeout_spin)
        cl.addLayout(row)
        il.addWidget(config)

        payload, pl = panel("Payload source")
        row = QHBoxLayout()
        self.payload_set_combo = QComboBox()
        self.payload_set_combo.addItems([str(i) for i in range(1, 11)])
        self.payload_set_combo.currentTextChanged.connect(self._on_payload_set_change)
        self.payload_combo = QComboBox()
        self.payload_combo.currentTextChanged.connect(self._on_payload_select)
        row.addWidget(self.payload_set_combo)
        row.addWidget(self.payload_combo, 1)
        pl.addLayout(row)
        self.payload_edit = QTextEdit()
        self.payload_edit.setObjectName("raw_request")
        self.payload_edit.setPlaceholderText("One payload per line")
        self.payload_edit.setFont(font)
        self.payload_edit.setMaximumHeight(130)
        self.payload_edit.textChanged.connect(self._on_payload_text_changed)
        self.payload_edit.textChanged.connect(self._update_payload_count)
        pl.addWidget(self.payload_edit)
        row = QHBoxLayout()
        load = QPushButton("Load file")
        load.clicked.connect(self._load_payload_file)
        self.lbl_payload_count = QLabel("0 payloads")
        self.lbl_payload_count.setStyleSheet("color:#84919d;")
        row.addWidget(load)
        row.addStretch()
        row.addWidget(self.lbl_payload_count)
        pl.addLayout(row)
        il.addWidget(payload)

        grep, gl = panel("Response match")
        self.grep_input = QLineEdit()
        self.grep_input.setPlaceholderText("Highlight matching responses…")
        gl.addWidget(self.grep_input)
        il.addWidget(grep)
        il.addStretch()
        main.addWidget(inspector)
        main.setSizes([680, 360])
        root.addWidget(main, 3)

        # Results workspace
        results, rl = panel("Attack results", "LIVE")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumHeight(7)
        rl.addWidget(self.progress_bar)

        stats = QHBoxLayout()
        self.lbl_done = QLabel("Done: 0")
        self.lbl_errors = QLabel("Errors: 0")
        self.lbl_elapsed = QLabel("")
        for label in (self.lbl_done, self.lbl_errors, self.lbl_elapsed):
            label.setStyleSheet("color:#84919d;font-size:11px;")
            stats.addWidget(label)
        stats.addStretch()
        clear = QPushButton("Clear")
        clear.clicked.connect(self._clear_results)
        stats.addWidget(clear)
        for text, fn in [
            ("Export CSV", self._export_csv),
            ("Export JSON", self._export_json),
            ("Import CSV", self._import_csv),
            ("Import JSON", self._import_json),
        ]:
            button = QPushButton(text)
            button.clicked.connect(fn)
            stats.addWidget(button)
        rl.addLayout(stats)

        self.results_table = QTableWidget(0, 6)
        self.results_table.setHorizontalHeaderLabels(
            ["#", "Payload", "Status", "Length", "Time (ms)", "Match"]
        )
        self.results_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setColumnWidth(0, 45)
        self.results_table.setColumnWidth(2, 65)
        self.results_table.setColumnWidth(3, 85)
        self.results_table.setColumnWidth(4, 85)
        self.results_table.setColumnWidth(5, 65)
        rl.addWidget(self.results_table, 1)
        root.addWidget(results, 2)

        self._attack_start = 0
        self._error_count = 0

    # ── Public API ─────────────────────────────
    def load_request(self, raw: str):
        self.request_edit.setPlainText(raw)

    # ── Private ────────────────────────────────
    def _load_payload_list(self):
        self.payload_combo.clear()
        self.payload_combo.addItem("— select category —")
        if os.path.isdir(PAYLOAD_DIR):
            for fname in sorted(os.listdir(PAYLOAD_DIR)):
                if fname.endswith(".txt"):
                    label = fname.replace(".txt", "").replace("_", " ").title()
                    self.payload_combo.addItem(label, userData=os.path.join(PAYLOAD_DIR, fname))

    def _on_payload_set_change(self, text):
        if not text.isdigit():
            return
        new_set = int(text)
        self._current_set = new_set
        self.payload_edit.blockSignals(True)
        self.payload_edit.setPlainText(self._payload_sets[new_set])
        self.payload_edit.blockSignals(False)
        self._update_payload_count()

    def _on_payload_text_changed(self):
        self._payload_sets[self._current_set] = self.payload_edit.toPlainText()
        self._update_payload_count()

    def _on_payload_select(self, text):
        if text.startswith("—"):
            return
        idx  = self.payload_combo.currentIndex()
        path = self.payload_combo.itemData(idx)
        if not path or not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self.payload_edit.setPlainText(content)
        except Exception as e:
            self.payload_edit.setPlainText(f"Error loading: {e}")
        self.payload_combo.setCurrentIndex(0)

    def _load_payload_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Payload File", PAYLOAD_DIR, "Text Files (*.txt);;All Files (*)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    self.payload_edit.setPlainText(f.read())
            except Exception as e:
                self.payload_edit.setPlainText(f"Error: {e}")

    def _update_payload_count(self):
        lines = [l for l in self.payload_edit.toPlainText().split("\n") if l.strip()]
        self.lbl_payload_count.setText(f"{len(lines)} payloads in Set {self._current_set}")

    def _add_marker(self):
        cursor = self.request_edit.textCursor()
        selected = cursor.selectedText()
        if selected:
            cursor.insertText(f"§{selected}§")
        else:
            cursor.insertText("§FUZZ§")

    def _clear_markers(self):
        text = self.request_edit.toPlainText()
        text = re.sub(r"§([^§]*)§", r"\1", text)
        self.request_edit.setPlainText(text)

    def _get_payloads_dict(self) -> dict:
        result = {}
        for k, v in self._payload_sets.items():
            lines = [l.strip() for l in v.split("\n") if l.strip()]
            if lines:
                result[k] = lines
        return result

    def _on_attack(self):
        raw_tpl  = self.request_edit.toPlainText().strip()
        payload_sets = self._get_payloads_dict()
        mode = self.mode_combo.currentText()

        if not raw_tpl:
            return
        if not payload_sets:
            return

        host    = self.host_input.text().strip() or "127.0.0.1"
        port    = self.port_input.value()
        use_ssl = self.ssl_check.isChecked()
        threads = self.threads_spin.value()
        timeout = self.timeout_spin.value()

        self._clear_results()
        self.btn_attack.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self._attack_start = time.time()

        self._thread = QThread()
        self._worker = AttackWorker(host, port, raw_tpl, mode, payload_sets, use_ssl, threads, timeout)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.result.connect(self._on_result)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_attack_done)
        self._worker.stopped.connect(self._on_attack_done)
        self._worker.finished.connect(self._thread.quit)
        self._worker.stopped.connect(self._thread.quit)
        self._thread.start()

    def _on_stop(self):
        if self._worker:
            self._worker.stop()

    def _on_result(self, idx: int, payload: str, status: int, length: int, ms: float):
        self._append_result(idx, payload, status, length, ms)

    def _on_progress(self, done: int, total: int):
        self.progress_bar.setValue(done)
        self.lbl_done.setText(f"Done: {done}/{total}")
        elapsed = time.time() - self._attack_start
        self.lbl_elapsed.setText(f"Elapsed: {elapsed:.1f}s")

    def _on_attack_done(self):
        self.btn_attack.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _clear_results(self):
        self.results_table.setRowCount(0)
        self._results.clear()
        self._error_count = 0
        self.progress_bar.setValue(0)
        self.lbl_done.setText("Done: 0")
        self.lbl_errors.setText("Errors: 0")
        self.lbl_elapsed.setText("")

    def _export_csv(self):
        if not self._results:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "intruder_results.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["idx","payload","status","length","ms"])
                writer.writeheader()
                writer.writerows(self._results)
        except Exception as e:
            pass

    def _export_json(self):
        if not self._results:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "intruder_results.json", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._results, f, indent=2, ensure_ascii=True)
        except Exception:
            pass

    def _import_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Results", "", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception:
            return
        if not rows:
            return
        self._clear_results()
        for row in rows:
            try:
                idx = int(row.get("idx", 0))
                payload = row.get("payload", "")
                status = int(row.get("status", 0)) if row.get("status") else 0
                length = int(row.get("length", 0)) if row.get("length") else 0
                ms = float(row.get("ms", 0)) if row.get("ms") else 0.0
            except Exception:
                continue
            self._append_result(idx, payload, status, length, ms)

    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Results", "", "JSON Files (*.json)"
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
        self._clear_results()
        for row in data:
            if not isinstance(row, dict):
                continue
            try:
                idx = int(row.get("idx", 0))
                payload = row.get("payload", "")
                status = int(row.get("status", 0)) if row.get("status") else 0
                length = int(row.get("length", 0)) if row.get("length") else 0
                ms = float(row.get("ms", 0)) if row.get("ms") else 0.0
            except Exception:
                continue
            self._append_result(idx, payload, status, length, ms)

    def _append_result(self, idx: int, payload: str, status: int, length: int, ms: float):
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)

        col_color = status_color(status) if status else "#82939B"
        match = ""

        items = [
            (str(idx + 1), Qt.AlignCenter, COLORS["text_dim"]),
            (payload[:80],  Qt.AlignLeft,   COLORS["yellow"]),
            (str(status) if status else "ERR", Qt.AlignCenter, col_color),
            (str(length),   Qt.AlignRight,  COLORS["text"]),
            (f"{ms:.1f}",   Qt.AlignRight,  COLORS["text"]),
            (match,         Qt.AlignCenter, COLORS["green"]),
        ]
        for col, (text, align, color) in enumerate(items):
            item = QTableWidgetItem(text)
            item.setTextAlignment(align | Qt.AlignVCenter)
            item.setForeground(QColor(color))
            self.results_table.setItem(row, col, item)

        if status == 0:
            self._error_count += 1
            self.lbl_errors.setText(f"Errors: {self._error_count}")

        self._results.append({
            "idx": idx, "payload": payload, "status": status,
            "length": length, "ms": ms
        })