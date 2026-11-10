"""
EXVOLT — Shared UI Components
Reusable building blocks for the EXVOLT design system.
All components use the design tokens from design_tokens.py.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QGraphicsDropShadowEffect, QToolTip
)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QColor, QFont, QPalette

from .design_tokens import (
    BACKGROUND, BACKGROUND_SECONDARY, SURFACE, SURFACE_ELEVATED,
    TEAL_PRIMARY, CYAN_PRIMARY, TEAL_MUTED,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    BORDER, BORDER_TEAL,
    SUCCESS, WARNING, DANGER, INFO,
    FONT_SANS, FONT_MONO,
    RADIUS_CARD, RADIUS_INPUT, RADIUS_BUTTON, RADIUS_BADGE,
    BORDER_WIDTH,
    SIDEBAR_WIDTH, SIDEBAR_ITEM_SIZE, SIDEBAR_ICON_SIZE,
    HEADER_HEIGHT, STATUS_BAR_HEIGHT, CARD_PADDING, CARD_GAP,
)


# ═══════════════════════════════════════════════════════════════════════════════
# GLASS CARD
# ═══════════════════════════════════════════════════════════════════════════════

class GlassCard(QFrame):
    """A dark glassmorphism card with subtle border and rounded corners."""

    def __init__(self, elevated: bool = False, parent=None):
        super().__init__(parent)
        self._elevated = elevated
        self.setObjectName("GlassCard")
        self._apply_style()

    def _apply_style(self):
        bg = SURFACE_ELEVATED if self._elevated else SURFACE
        border = BORDER_TEAL if self._elevated else BORDER
        self.setStyleSheet(f"""
            QFrame#GlassCard {{
                background-color: {bg};
                border: {BORDER_WIDTH}px solid {border};
                border-radius: {RADIUS_CARD}px;
            }}
        """)

    def setContentLayout(self, layout):
        """Set the internal content layout with standard card padding."""
        container = QWidget()
        container.setLayout(layout)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(CARD_PADDING, CARD_PADDING, CARD_PADDING, CARD_PADDING)
        outer.setSpacing(CARD_GAP)
        outer.addWidget(container)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION HEADER
# ═══════════════════════════════════════════════════════════════════════════════

class SectionHeader(QWidget):
    """A section title with optional teal accent line."""

    def __init__(self, title: str, subtitle: str = "", accent: str = TEAL_PRIMARY, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("SectionTitle")
        self.title_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-family: '{FONT_SANS}'; "
            f"font-size: 18px; font-weight: 700; letter-spacing: -0.5px;"
        )
        layout.addWidget(self.title_label)

        if subtitle:
            self.sub_label = QLabel(subtitle)
            self.sub_label.setObjectName("SectionSubtitle")
            self.sub_label.setStyleSheet(
                f"color: {TEXT_SECONDARY}; font-family: '{FONT_SANS}'; "
                f"font-size: 12px; font-weight: 400;"
            )
            layout.addWidget(self.sub_label)

        # Accent underline
        self._accent = QFrame()
        self._accent.setFixedHeight(2)
        self._accent.setStyleSheet(f"background-color: {accent}; border: none; border-radius: 1px;")
        self._accent.setFixedWidth(0)  # Hidden by default, can be animated
        layout.addWidget(self._accent)

    def show_accent(self, width: int = 32):
        self._accent.setFixedWidth(width)

    def hide_accent(self):
        self._accent.setFixedWidth(0)


# ═══════════════════════════════════════════════════════════════════════════════
# METRIC CARD
# ═══════════════════════════════════════════════════════════════════════════════

class MetricCard(GlassCard):
    """A KPI metric card: large value, compact label, teal accent."""

    def __init__(self, label: str, value: str, accent: str = TEAL_PRIMARY, parent=None):
        super().__init__(elevated=True, parent=parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.label_lbl = QLabel(label.upper())
        self.label_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-family: '{FONT_SANS}'; "
            f"font-size: 11px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;"
        )
        layout.addWidget(self.label_lbl)

        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("MetricValue")
        self.value_lbl.setStyleSheet(
            f"color: {accent}; font-family: '{FONT_SANS}'; "
            f"font-size: 28px; font-weight: 800;"
        )
        layout.addWidget(self.value_lbl)

        layout.addStretch()
        self.setContentLayout(layout)

    def set_value(self, value: str):
        self.value_lbl.setText(value)

    def set_label(self, label: str):
        self.label_lbl.setText(label.upper())


# ═══════════════════════════════════════════════════════════════════════════════
# STATUS BADGE
# ═══════════════════════════════════════════════════════════════════════════════

class StatusBadge(QLabel):
    """A small colored status badge."""

    def __init__(self, text: str, color: str = TEAL_PRIMARY, parent=None):
        super().__init__(text, parent)
        self.setObjectName("StatusBadge")
        self.setStyleSheet(
            f"QLabel#StatusBadge {{"
            f"  color: {TEXT_PRIMARY};"
            f"  background-color: {color}22;"
            f"  border: 1px solid {color}44;"
            f"  border-radius: {RADIUS_BADGE}px;"
            f"  padding: 2px 8px;"
            f"  font-family: '{FONT_SANS}';"
            f"  font-size: 10px;"
            f"  font-weight: 700;"
            f"}}"
        )
        self.setAlignment(Qt.AlignCenter)


# ═══════════════════════════════════════════════════════════════════════════════
# ICON BUTTON
# ═══════════════════════════════════════════════════════════════════════════════

class IconButton(QPushButton):
    """A compact icon-only button with hover/active states."""

    def __init__(self, icon_text: str = "", tooltip: str = "", active: bool = False, parent=None):
        super().__init__(icon_text, parent)
        self._icon_text = icon_text
        self._active = active
        self.setToolTip(tooltip)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(SIDEBAR_ITEM_SIZE, SIDEBAR_ITEM_SIZE)
        self.setCheckable(True)
        self.setChecked(active)
        self._apply_style()

    def _apply_style(self):
        if self._active:
            bg = TEAL_PRIMARY
            color = BACKGROUND
            border = TEAL_PRIMARY
        else:
            bg = "transparent"
            color = TEXT_SECONDARY
            border = "transparent"

        self.setStyleSheet(
            f"QPushButton {{"
            f"  color: {color};"
            f"  background-color: {bg};"
            f"  border: 1px solid {border};"
            f"  border-radius: {RADIUS_BUTTON}px;"
            f"  font-size: {SIDEBAR_ICON_SIZE}px;"
            f"  font-weight: 600;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {SURFACE_ELEVATED};"
            f"  border: 1px solid {BORDER_TEAL};"
            f"  color: {TEXT_PRIMARY};"
            f"}}"
            f"QPushButton:checked {{"
            f"  background-color: {TEAL_PRIMARY};"
            f"  color: {BACKGROUND};"
            f"  border: 1px solid {TEAL_PRIMARY};"
            f"}}"
        )

    def set_active(self, active: bool):
        self._active = active
        self.setChecked(active)
        self._apply_style()


# ═══════════════════════════════════════════════════════════════════════════════
# PRIMARY BUTTON
# ═══════════════════════════════════════════════════════════════════════════════

class PrimaryButton(QPushButton):
    """Teal primary action button."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(
            f"QPushButton {{"
            f"  color: {BACKGROUND};"
            f"  background-color: {TEAL_PRIMARY};"
            f"  border: none;"
            f"  border-radius: {RADIUS_BUTTON}px;"
            f"  padding: 6px 16px;"
            f"  font-family: '{FONT_SANS}';"
            f"  font-size: 12px;"
            f"  font-weight: 700;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {CYAN_PRIMARY};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {TEAL_MUTED};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background-color: {TEXT_MUTED}33;"
            f"  color: {TEXT_MUTED};"
            f"}}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECONDARY BUTTON
# ═══════════════════════════════════════════════════════════════════════════════

class SecondaryButton(QPushButton):
    """Subtle surface button for secondary actions."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(
            f"QPushButton {{"
            f"  color: {TEXT_PRIMARY};"
            f"  background-color: {SURFACE_ELEVATED};"
            f"  border: 1px solid {BORDER};"
            f"  border-radius: {RADIUS_BUTTON}px;"
            f"  padding: 6px 16px;"
            f"  font-family: '{FONT_SANS}';"
            f"  font-size: 12px;"
            f"  font-weight: 600;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {SURFACE};"
            f"  border: 1px solid {BORDER_TEAL};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {TEAL_MUTED};"
            f"}}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TOOLBAR
# ═══════════════════════════════════════════════════════════════════════════════

class Toolbar(QFrame):
    """A compact horizontal toolbar with glass surface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Toolbar")
        self.setFixedHeight(HEADER_HEIGHT)
        self.setStyleSheet(
            f"QFrame#Toolbar {{"
            f"  background-color: {SURFACE};"
            f"  border-bottom: 1px solid {BORDER};"
            f"}}"
        )
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(16, 0, 16, 0)
        self._layout.setSpacing(12)

    def add_widget(self, widget):
        self._layout.addWidget(widget)

    def add_stretch(self):
        self._layout.addStretch()

    def add_spacing(self, px: int):
        self._layout.addSpacing(px)


# ═══════════════════════════════════════════════════════════════════════════════
# DARK TABLE
# ═══════════════════════════════════════════════════════════════════════════════

class DarkTable(QFrame):
    """A styled QTableWidget wrapper with dark glass appearance."""

    def __init__(self, headers: list, parent=None):
        super().__init__(parent)
        from PyQt5.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView
        from PyQt5.QtCore import Qt

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        self.table.setStyleSheet(
            f"QTableWidget {{"
            f"  background-color: {SURFACE};"
            f"  color: {TEXT_SECONDARY};"
            f"  border: 1px solid {BORDER};"
            f"  border-radius: {RADIUS_CARD}px;"
            f"  gridline-color: transparent;"
            f"  selection-background-color: {TEAL_PRIMARY}22;"
            f"}}"
            f"QTableWidget::item {{"
            f"  padding: 6px 10px;"
            f"  border: none;"
            f"}}"
            f"QTableWidget::item:selected {{"
            f"  background-color: {TEAL_PRIMARY}22;"
            f"  color: {TEXT_PRIMARY};"
            f"}}"
            f"QHeaderView::section {{"
            f"  background-color: {BACKGROUND_SECONDARY};"
            f"  color: {TEXT_MUTED};"
            f"  border: none;"
            f"  border-bottom: 1px solid {BORDER};"
            f"  padding: 6px 10px;"
            f"  font-family: '{FONT_SANS}';"
            f"  font-size: 11px;"
            f"  font-weight: 600;"
            f"  text-transform: uppercase;"
            f"  letter-spacing: 0.5px;"
            f"}}"
        )

        layout.addWidget(self.table)

    def set_row_count(self, count: int):
        self.table.setRowCount(count)

    def set_item(self, row: int, col: int, item):
        self.table.setItem(row, col, item)

    def item(self, row: int, col: int):
        return self.table.item(row, col)

    def row_count(self) -> int:
        return self.table.rowCount()

    def insert_row(self, row: int):
        self.table.insertRow(row)

    def remove_row(self, row: int):
        self.table.removeRow(row)

    def clear_contents(self):
        self.table.setRowCount(0)

    def set_column_width(self, col: int, width: int):
        self.table.setColumnWidth(col, width)

    def set_selection_mode(self, mode):
        self.table.setSelectionMode(mode)

    def set_selection_behavior(self, behavior):
        self.table.setSelectionBehavior(behavior)

    def current_cell_changed(self, callback):
        self.table.currentCellChanged.connect(callback)

    def set_context_menu_policy(self, policy):
        self.table.setContextMenuPolicy(policy)

    def custom_context_menu_requested(self, callback):
        self.table.customContextMenuRequested.connect(callback)

    def double_clicked(self, callback):
        self.table.doubleClicked.connect(callback)


# ═══════════════════════════════════════════════════════════════════════════════
# DARK EDITOR
# ═══════════════════════════════════════════════════════════════════════════════

class DarkEditor(QFrame):
    """A monospace code editor with dark glass surface."""

    def __init__(self, placeholder: str = "", read_only: bool = False, parent=None):
        super().__init__(parent)
        from PyQt5.QtWidgets import QTextEdit, QVBoxLayout
        from PyQt5.QtGui import QFont

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText(placeholder)
        self.editor.setReadOnly(read_only)
        self.editor.setFont(QFont(FONT_MONO, 11))
        self.editor.setStyleSheet(
            f"QTextEdit {{"
            f"  background-color: {BACKGROUND};"
            f"  color: {TEXT_PRIMARY};"
            f"  border: 1px solid {BORDER};"
            f"  border-radius: {RADIUS_INPUT}px;"
            f"  font-family: '{FONT_MONO}';"
            f"  font-size: 12px;"
            f"  padding: 8px;"
            f"  selection-background-color: {TEAL_PRIMARY}33;"
            f"}}"
            f"QTextEdit:focus {{"
            f"  border: 1px solid {BORDER_TEAL};"
            f"}}"
        )

        layout.addWidget(self.editor)

    def to_plain_text(self) -> str:
        return self.editor.toPlainText()

    def set_plain_text(self, text: str):
        self.editor.setPlainText(text)

    def set_read_only(self, readonly: bool):
        self.editor.setReadOnly(readonly)

    def set_placeholder(self, text: str):
        self.editor.setPlaceholderText(text)

    def document(self):
        return self.editor.document()


# ═══════════════════════════════════════════════════════════════════════════════
# PROGRESS INDICATOR
# ═══════════════════════════════════════════════════════════════════════════════

class ProgressIndicator(QFrame):
    """A compact horizontal progress bar with teal fill."""

    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt5.QtWidgets import QVBoxLayout, QProgressBar

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setFixedHeight(6)
        self.bar.setTextVisible(False)
        self.bar.setStyleSheet(
            f"QProgressBar {{"
            f"  background-color: {SURFACE_ELEVATED};"
            f"  border: none;"
            f"  border-radius: 3px;"
            f"  text-align: center;"
            f"}}"
            f"QProgressBar::chunk {{"
            f"  background-color: {TEAL_PRIMARY};"
            f"  border-radius: 3px;"
            f"}}"
        )

        layout.addWidget(self.bar)

    def set_value(self, value: int):
        self.bar.setValue(value)

    def set_range(self, minimum: int, maximum: int):
        self.bar.setRange(minimum, maximum)


# ═══════════════════════════════════════════════════════════════════════════════
# EMPTY STATE
# ═══════════════════════════════════════════════════════════════════════════════

class EmptyState(QWidget):
    """A neutral empty-state illustration with text."""

    def __init__(self, icon: str = "—", title: str = "No data", subtitle: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 48px; font-weight: 400;"
        )
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_lbl)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-family: '{FONT_SANS}'; "
            f"font-size: 16px; font-weight: 600;"
        )
        self.title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_lbl)

        if subtitle:
            self.sub_lbl = QLabel(subtitle)
            self.sub_lbl.setStyleSheet(
                f"color: {TEXT_SECONDARY}; font-family: '{FONT_SANS}'; "
                f"font-size: 12px;"
            )
            self.sub_lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.sub_lbl)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR ITEM
# ═══════════════════════════════════════════════════════════════════════════════

class SidebarItem(QWidget):
    """A single sidebar navigation item: icon + tooltip."""

    def __init__(self, icon_text: str, page_name: str, active: bool = False, parent=None):
        super().__init__(parent)
        self._page_name = page_name
        self._active = active

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        self.btn = IconButton(icon_text, tooltip=page_name, active=active)
        layout.addWidget(self.btn)

        self.setFixedSize(SIDEBAR_WIDTH, SIDEBAR_ITEM_SIZE + 8)
        self.setCursor(Qt.PointingHandCursor)

    def button(self) -> IconButton:
        return self.btn

    def set_active(self, active: bool):
        self._active = active
        self.btn.set_active(active)

    def page_name(self) -> str:
        return self._page_name


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ═══════════════════════════════════════════════════════════════════════════════

class PageHeader(QWidget):
    """Page title header with workspace name and current page title."""

    def __init__(self, workspace: str = "EXVOLT", title: str = "Dashboard", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.workspace_lbl = QLabel(workspace.upper())
        self.workspace_lbl.setStyleSheet(
            f"color: {TEAL_PRIMARY}; font-family: '{FONT_SANS}'; "
            f"font-size: 11px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;"
        )
        layout.addWidget(self.workspace_lbl)

        divider = QLabel("•")
        divider.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(divider)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-family: '{FONT_SANS}'; "
            f"font-size: 20px; font-weight: 700;"
        )
        layout.addWidget(self.title_lbl)

        layout.addStretch()

    def set_title(self, title: str):
        self.title_lbl.setText(title)