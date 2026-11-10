"""
EXVOLT — Sidebar Navigation
Compact icon-only sidebar (64–76px) with teal active states and tooltips.
Navigates to existing application pages only.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from .design_tokens import (
    BACKGROUND, SURFACE, SURFACE_ELEVATED, TEAL_PRIMARY,
    TEXT_PRIMARY, TEXT_SECONDARY, BORDER, BORDER_TEAL,
    SIDEBAR_WIDTH, SIDEBAR_ITEM_SIZE, SIDEBAR_ICON_SIZE,
)
from .components import SidebarItem, GlassCard


# Navigation entries: (icon_text, page_name, page_key)
# Only entries that map to existing VersSuite features are included.
SIDEBAR_ENTRIES = [
    ("▶", "Proxy / Intercept", "proxy"),
    ("↻", "Repeater", "repeater"),
    ("⚡", "Intruder", "intruder"),
    ("⇄", "Comparer", "comparer"),
    ("🔬", "Sequencer", "sequencer"),
    ("🔌", "WebSocket", "websocket"),
    ("🔧", "Decoder", "decoder"),
    ("📜", "History", "history"),
    ("ℹ", "About", "about"),
]

BOTTOM_ENTRIES = [
    ("⚙", "Settings", "settings"),
    ("?", "About", "about"),
]


class Sidebar(QFrame):
    """
    Compact icon-only sidebar.
    Emits page_changed(str) when a navigation item is selected.
    """

    page_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self.setStyleSheet(
            f"QFrame#Sidebar {{"
            f"  background-color: {SURFACE};"
            f"  border-right: 1px solid {BORDER};"
            f"}}"
        )

        self._items: dict[str, SidebarItem] = {}
        self._active_key: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(4)

        # ── Logo (top) ──
        self.logo = QLabel("EXVOLT")
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setStyleSheet(
            f"color: {TEAL_PRIMARY}; font-family: 'Inter, Segoe UI, sans-serif'; "
            f"font-size: 16px; font-weight: 800; letter-spacing: 1px;"
        )
        self.logo.setFixedHeight(40)
        layout.addWidget(self.logo)

        # Small accent under logo
        logo_accent = QFrame()
        logo_accent.setFixedHeight(2)
        logo_accent.setFixedWidth(28)
        logo_accent.setStyleSheet(f"background-color: {TEAL_PRIMARY}; border: none; border-radius: 1px;")
        logo_accent_container = QWidget()
        logo_accent_l = QHBoxLayout(logo_accent_container)
        logo_accent_l.setContentsMargins(0, 0, 0, 0)
        logo_accent_l.addStretch()
        logo_accent_l.addWidget(logo_accent)
        logo_accent_l.addStretch()
        layout.addWidget(logo_accent_container)

        layout.addSpacing(16)

        # ── Navigation entries ──
        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-family: 'Inter, Segoe UI, sans-serif'; "
            f"font-size: 10px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;"
        )
        nav_label.setFixedHeight(20)
        layout.addWidget(nav_label)

        self.nav_container = QWidget()
        self.nav_layout = QVBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(8, 0, 8, 0)
        self.nav_layout.setSpacing(6)

        for icon, name, key in SIDEBAR_ENTRIES:
            item = SidebarItem(icon, name, active=(key == "proxy"))
            item.button().clicked.connect(lambda checked, k=key: self._on_item_clicked(k))
            self._items[key] = item
            self.nav_layout.addWidget(item)

        self.nav_layout.addStretch()
        layout.addWidget(self.nav_container)

        # ── Bottom entries ──
        bottom_label = QLabel("SYSTEM")
        bottom_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-family: 'Inter, Segoe UI, sans-serif'; "
            f"font-size: 10px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;"
        )
        bottom_label.setFixedHeight(20)
        layout.addWidget(bottom_label)

        self.bottom_container = QWidget()
        self.bottom_layout = QVBoxLayout(self.bottom_container)
        self.bottom_layout.setContentsMargins(8, 0, 8, 0)
        self.bottom_layout.setSpacing(6)

        for icon, name, key in BOTTOM_ENTRIES:
            item = SidebarItem(icon, name, active=False)
            item.button().clicked.connect(lambda checked, k=key: self._on_item_clicked(k))
            self._items[key] = item
            self.bottom_layout.addWidget(item)

        self.bottom_layout.addStretch()
        layout.addWidget(self.bottom_container)

        layout.addStretch()

    def _on_item_clicked(self, key: str):
        if key == self._active_key:
            return
        self.set_active(key)
        self.page_changed.emit(key)

    def set_active(self, key: str):
        """Set the active sidebar item by page key."""
        if self._active_key and self._active_key in self._items:
            self._items[self._active_key].set_active(False)
        if key in self._items:
            self._items[key].set_active(True)
        self._active_key = key

    def active_page(self) -> str | None:
        return self._active_key