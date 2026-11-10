"""
EXVOLT — Top Header / Workspace Bar
Contains workspace name, page title, proxy status, host/port controls,
start/stop proxy, intercept toggles, and search.
All original proxy callbacks are preserved and connected.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit, QSpinBox,
    QFrame, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from .design_tokens import (
    BACKGROUND, SURFACE, SURFACE_ELEVATED, TEAL_PRIMARY, CYAN_PRIMARY,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER, BORDER_TEAL,
    SUCCESS, DANGER, INFO, FONT_SANS, FONT_MONO,
    HEADER_HEIGHT,
)
from .components import PrimaryButton, SecondaryButton, StatusBadge


class Header(QWidget):
    """
    Premium compact header for EXVOLT.
    
    Signals:
        start_proxy(host, port)
        stop_proxy()
        toggle_intercept(checked)
        toggle_response_intercept(checked)
        search_changed(text)
    """

    start_proxy = pyqtSignal(str, int)
    stop_proxy = pyqtSignal()
    toggle_intercept = pyqtSignal(bool)
    toggle_response_intercept = pyqtSignal(bool)
    search_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Header")
        self.setFixedHeight(HEADER_HEIGHT)
        self.setStyleSheet(
            f"QFrame#Header {{"
            f"  background-color: {SURFACE};"
            f"  border-bottom: 1px solid {BORDER};"
            f"}}"
        )

        self._proxy_running = False
        self._intercept_on = False
        self._resp_intercept_on = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # ── Workspace brand ──
        self.brand = QLabel("EXVOLT")
        self.brand.setObjectName("HeaderBrand")
        self.brand.setStyleSheet(
            f"color: {TEAL_PRIMARY}; font-family: '{FONT_SANS}'; "
            f"font-size: 18px; font-weight: 800; letter-spacing: 0.5px;"
        )
        layout.addWidget(self.brand)

        # Page title (updated by MainWindow when page changes)
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("HeaderPageTitle")
        self.page_title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-family: '{FONT_SANS}'; "
            f"font-size: 14px; font-weight: 600;"
        )
        layout.addWidget(self.page_title)

        layout.addSpacing(8)

        # Divider
        div1 = QFrame()
        div1.setFrameShape(QFrame.VLine)
        div1.setStyleSheet(f"color: {BORDER};")
        layout.addWidget(div1)

        # ── Proxy status indicator ──
        self.status_indicator = StatusBadge("PROXY: STOPPED", color=DANGER)
        layout.addWidget(self.status_indicator)

        layout.addSpacing(8)

        # Divider
        div2 = QFrame()
        div2.setFrameShape(QFrame.VLine)
        div2.setStyleSheet(f"color: {BORDER};")
        layout.addWidget(div2)

        # ── Host / Port ──
        layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit("127.0.0.1")
        self.host_input.setMaximumWidth(140)
        self.host_input.setToolTip("Proxy listen host")
        self.host_input.setStyleSheet(
            f"QLineEdit {{"
            f"  background-color: {BACKGROUND};"
            f"  color: {TEXT_PRIMARY};"
            f"  border: 1px solid {BORDER};"
            f"  border-radius: {4}px;"
            f"  padding: 4px 8px;"
            f"  font-family: '{FONT_SANS}';"
            f"  font-size: 12px;"
            f"}}"
        )
        layout.addWidget(self.host_input)

        layout.addWidget(QLabel("Port:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(8080)
        self.port_input.setMaximumWidth(70)
        self.port_input.setToolTip("Proxy listen port")
        self.port_input.setStyleSheet(
            f"QSpinBox {{"
            f"  background-color: {BACKGROUND};"
            f"  color: {TEXT_PRIMARY};"
            f"  border: 1px solid {BORDER};"
            f"  border-radius: {4}px;"
            f"  padding: 4px 8px;"
            f"  font-family: '{FONT_SANS}';"
            f"  font-size: 12px;"
            f"}}"
        )
        layout.addWidget(self.port_input)

        layout.addSpacing(8)

        # ── Start / Stop Proxy ──
        self.btn_start = PrimaryButton("Start Proxy")
        self.btn_start.setToolTip("Start the proxy listener")
        self.btn_start.clicked.connect(self._on_start)
        layout.addWidget(self.btn_start)

        self.btn_stop = SecondaryButton("Stop")
        self.btn_stop.setToolTip("Stop the proxy listener")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop)
        layout.addWidget(self.btn_stop)

        layout.addSpacing(8)

        # Divider
        div3 = QFrame()
        div3.setFrameShape(QFrame.VLine)
        div3.setStyleSheet(f"color: {BORDER};")
        layout.addWidget(div3)

        # ── Intercept toggles ──
        self.btn_intercept = QPushButton("Intercept: OFF")
        self.btn_intercept.setCheckable(True)
        self.btn_intercept.setToolTip("Toggle request interception")
        self.btn_intercept.clicked.connect(self._on_intercept_toggle)
        self.btn_intercept.setStyleSheet(
            f"QPushButton {{"
            f"  color: {TEXT_SECONDARY};"
            f"  background-color: {SURFACE_ELEVATED};"
            f"  border: 1px solid {BORDER};"
            f"  border-radius: {4}px;"
            f"  padding: 4px 12px;"
            f"  font-family: '{FONT_SANS}';"
            f"  font-size: 12px;"
            f"  font-weight: 600;"
            f"}}"
            f"QPushButton:checked {{"
            f"  color: {BACKGROUND};"
            f"  background-color: {TEAL_PRIMARY};"
            f"  border: 1px solid {TEAL_PRIMARY};"
            f"}}"
        )
        layout.addWidget(self.btn_intercept)

        self.btn_resp_intercept = QPushButton("Resp Int: OFF")
        self.btn_resp_intercept.setCheckable(True)
        self.btn_resp_intercept.setToolTip("Toggle response interception")
        self.btn_resp_intercept.clicked.connect(self._on_resp_intercept_toggle)
        self.btn_resp_intercept.setStyleSheet(
            f"QPushButton {{"
            f"  color: {TEXT_SECONDARY};"
            f"  background-color: {SURFACE_ELEVATED};"
            f"  border: 1px solid {BORDER};"
            f"  border-radius: {4}px;"
            f"  padding: 4px 12px;"
            f"  font-family: '{FONT_SANS}';"
            f"  font-size: 12px;"
            f"  font-weight: 600;"
            f"}}"
            f"QPushButton:checked {{"
            f"  color: {BACKGROUND};"
            f"  background-color: {CYAN_PRIMARY};"
            f"  border: 1px solid {CYAN_PRIMARY};"
            f"}}"
        )
        layout.addWidget(self.btn_resp_intercept)

        layout.addStretch()

        # ── Search ──
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search…")
        self.search.setMaximumWidth(240)
        self.search.setStyleSheet(
            f"QLineEdit {{"
            f"  background-color: {BACKGROUND};"
            f"  color: {TEXT_PRIMARY};"
            f"  border: 1px solid {BORDER};"
            f"  border-radius: {4}px;"
            f"  padding: 4px 10px;"
            f"  font-family: '{FONT_SANS}';"
            f"  font-size: 12px;"
            f"}}"
            f"QLineEdit:focus {{"
            f"  border: 1px solid {BORDER_TEAL};"
            f"}}"
        )
        self.search.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search)

    # ── Public API ──
    def set_page_title(self, title: str):
        self.page_title.setText(title)

    def set_proxy_running(self, running: bool):
        self._proxy_running = running
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        if running:
            self.status_indicator.setText("PROXY: RUNNING")
            self.status_indicator.setStyleSheet(
                f"QLabel#StatusBadge {{"
                f"  color: {BACKGROUND};"
                f"  background-color: {SUCCESS}22;"
                f"  border: 1px solid {SUCCESS}44;"
                f"  border-radius: {4}px;"
                f"  padding: 2px 8px;"
                f"  font-family: '{FONT_SANS}';"
                f"  font-size: 10px;"
                f"  font-weight: 700;"
                f"}}"
            )
        else:
            self.status_indicator.setText("PROXY: STOPPED")
            self.status_indicator.setStyleSheet(
                f"QLabel#StatusBadge {{"
                f"  color: {TEXT_PRIMARY};"
                f"  background-color: {DANGER}22;"
                f"  border: 1px solid {DANGER}44;"
                f"  border-radius: {4}px;"
                f"  padding: 2px 8px;"
                f"  font-family: '{FONT_SANS}';"
                f"  font-size: 10px;"
                f"  font-weight: 700;"
                f"}}"
            )

    def set_intercept(self, enabled: bool):
        self._intercept_on = enabled
        self.btn_intercept.setChecked(enabled)
        self.btn_intercept.setText(f"Intercept: {'ON' if enabled else 'OFF'}")

    def set_response_intercept(self, enabled: bool):
        self._resp_intercept_on = enabled
        self.btn_resp_intercept.setChecked(enabled)
        self.btn_resp_intercept.setText(f"Resp Int: {'ON' if enabled else 'OFF'}")

    def host(self) -> str:
        return self.host_input.text().strip() or "127.0.0.1"

    def port(self) -> int:
        return self.port_input.value()

    # ── Internal slots ──
    def _on_start(self):
        self.start_proxy.emit(self.host(), self.port())

    def _on_stop(self):
        self.stop_proxy.emit()

    def _on_intercept_toggle(self, checked: bool):
        self.toggle_intercept.emit(checked)

    def _on_resp_intercept_toggle(self, checked: bool):
        self.toggle_response_intercept.emit(checked)