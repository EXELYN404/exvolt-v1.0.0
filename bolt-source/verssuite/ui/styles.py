# EXVOLT — Graphite Interface / Emerald Accent

COLORS = {
    "bg": "#0b0e12",
    "bg2": "#10151b",
    "border": "#242d36",
    "accent": "#36d69a",
    "green": "#36d69a",
    "red": "#ff647c",
    "purple": "#ad91ff",
    "yellow": "#f0c674",
    "blue": "#78b7ff",
    "orange": "#ffad70",
    "text": "#e8edf3",
    "text_dim": "#82909e",
    "text_code": "#cbd8e5",
}

STATUS_COLORS = {
    "2xx": "#36d69a",
    "3xx": "#78b7ff",
    "4xx": "#f0c674",
    "5xx": "#ff647c",
}

def status_color(code):
    try:
        code = int(code)
    except (TypeError, ValueError):
        return COLORS["text_dim"]
    if 200 <= code < 300:
        return STATUS_COLORS["2xx"]
    if 300 <= code < 400:
        return STATUS_COLORS["3xx"]
    if 400 <= code < 500:
        return STATUS_COLORS["4xx"]
    if 500 <= code < 600:
        return STATUS_COLORS["5xx"]
    return COLORS["text_dim"]

DARK_STYLESHEET = """
* {
    font-family: "Inter", "Noto Sans", sans-serif;
    font-size: 12px;
    outline: none;
}
QMainWindow, QWidget {
    background: #0b0e12;
    color: #dce4ec;
}
QWidget#exvoltRoot { background: #0b0e12; }
QWidget#mainBody { background: #0b0e12; }
QWidget#sidebar {
    background: #0e1318;
    border-right: 1px solid #222b34;
}
QLabel#sidebarBrand {
    color: #36d69a;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 2px;
    padding: 8px 7px 2px;
}
QLabel#sidebarCaption {
    color: #647381;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.5px;
    padding: 0 8px;
}
QLabel#sidebarFooter {
    color: #53616e;
    font-size: 9px;
    letter-spacing: 1px;
    padding: 10px 7px;
}
QPushButton#navButton {
    text-align: left;
    background: transparent;
    color: #8997a5;
    border: 0;
    border-radius: 6px;
    padding: 11px 12px;
    margin: 1px 0;
    font-weight: 500;
}
QPushButton#navButton:hover {
    background: #171f26;
    color: #dce4ec;
}
QPushButton#navButton:checked {
    background: #14271f;
    color: #36d69a;
    border-left: 2px solid #36d69a;
    padding-left: 10px;
    font-weight: 650;
}
QMenuBar {
    background: #0e1318;
    color: #8997a5;
    border-bottom: 1px solid #222b34;
    padding: 2px 4px;
}
QMenuBar::item { padding: 7px 12px; background: transparent; }
QMenuBar::item:selected { background: #19221f; color: #36d69a; border-radius: 4px; }
QMenu {
    background: #151b22;
    color: #dce4ec;
    border: 1px solid #303b46;
    padding: 5px;
}
QMenu::item { padding: 8px 28px; border-radius: 4px; }
QMenu::item:selected { background: #1b3027; color: #36d69a; }
QMenu::separator { height: 1px; background: #29343e; margin: 5px 8px; }

QTabWidget::pane {
    background: #0b0e12;
    border: 0;
    top: -1px;
}
QTabBar {
    background: #0e1318;
    border: 0;
}
QTabBar::tab {
    background: #0e1318;
    color: #71808e;
    padding: 10px 16px;
    border: 0;
    border-bottom: 2px solid transparent;
    margin-right: 1px;
}
QTabBar::tab:selected {
    color: #36d69a;
    background: #111a17;
    border-bottom: 2px solid #36d69a;
}
QTabBar::tab:hover:!selected { color: #cbd5df; background: #151c22; }

QPushButton {
    background: #171e25;
    color: #cbd5df;
    border: 1px solid #2a3540;
    border-radius: 5px;
    padding: 7px 12px;
    min-height: 16px;
}
QPushButton:hover { background: #202a33; border-color: #3a4a57; color: #edf3f8; }
QPushButton:pressed { background: #14251d; border-color: #28684f; }
QPushButton:checked {
    background: #173126;
    color: #36d69a;
    border-color: #28684f;
}
QPushButton:disabled { color: #4d5a66; background: #11161b; border-color: #202830; }

QToolButton {
    background: transparent;
    color: #8b99a7;
    border: 0;
    border-radius: 4px;
    padding: 5px;
}
QToolButton:hover { background: #202a33; color: #e4edf5; }
QToolButton:checked { color: #36d69a; background: #172820; }

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateTimeEdit {
    background: #10161c;
    color: #dce4ec;
    border: 1px solid #29343f;
    border-radius: 5px;
    padding: 7px 9px;
    selection-background-color: #245b47;
    min-height: 16px;
}
QLineEdit:hover, QComboBox:hover { border-color: #394854; }
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QDateTimeEdit:focus {
    border-color: #318b67;
    background: #111a1b;
}
QLineEdit:disabled { color: #596673; background: #0e1318; }

QComboBox::drop-down { border: 0; width: 22px; }
QComboBox QAbstractItemView {
    background: #151c22;
    color: #dce4ec;
    border: 1px solid #303b46;
    selection-background-color: #1c3529;
    selection-color: #36d69a;
    padding: 4px;
}
QSpinBox::up-button, QSpinBox::down-button {
    background: #171e25;
    border: 0;
    width: 16px;
}

QTextEdit, QPlainTextEdit {
    background: #0d1217;
    color: #cbd8e5;
    border: 1px solid #222c35;
    border-radius: 4px;
    selection-background-color: #245b47;
    selection-color: #f0f7f3;
}
QTextEdit:focus, QPlainTextEdit:focus { border-color: #2a5142; }
QTextEdit QScrollBar, QPlainTextEdit QScrollBar { background: transparent; }

QTableWidget, QTableView, QTreeWidget, QTreeView, QListWidget, QListView {
    background: #0d1217;
    alternate-background-color: #111820;
    color: #cbd5df;
    border: 1px solid #222c35;
    border-radius: 4px;
    gridline-color: #1b242c;
    selection-background-color: #183328;
    selection-color: #36d69a;
}
QTableWidget::item, QTreeWidget::item { padding: 5px 7px; }
QTableWidget::item:hover, QTreeWidget::item:hover { background: #151f25; }
QHeaderView { background: #11171d; }
QHeaderView::section {
    background: #121920;
    color: #7f8e9c;
    border: 0;
    border-right: 1px solid #202a33;
    border-bottom: 1px solid #28333d;
    padding: 9px 8px;
    font-weight: 600;
}
QTableCornerButton::section { background: #121920; border: 0; }
QTreeWidget::branch { background: #0e1419; }

QGroupBox {
    background: #10161b;
    border: 1px solid #26313a;
    border-radius: 6px;
    margin-top: 12px;
    padding: 10px 8px 8px;
    font-weight: 600;
    color: #9eacb9;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #36d69a;
}
QFrame[frameShape="4"], QFrame[frameShape="5"] { color: #222c35; }

QSplitter::handle { background: #202a33; }
QSplitter::handle:hover { background: #36d69a; }
QSplitter::handle:horizontal { width: 3px; }
QSplitter::handle:vertical { height: 3px; }

QScrollBar:vertical {
    background: transparent;
    width: 9px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2b3742;
    min-height: 28px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover { background: #435562; }
QScrollBar:horizontal { background: transparent; height: 9px; margin: 0; }
QScrollBar::handle:horizontal {
    background: #2b3742;
    min-width: 28px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover { background: #435562; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }

QStatusBar {
    background: #0e1318;
    color: #788795;
    border-top: 1px solid #222b34;
    padding: 3px 7px;
}
QStatusBar::item { border: 0; }
QLabel#status_err { color: #ff647c; font-weight: 600; }
QLabel#status_ok { color: #36d69a; font-weight: 600; }

QCheckBox, QRadioButton { spacing: 8px; color: #aebbc7; }
QCheckBox::indicator, QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #35434d;
    background: #10161b;
}
QCheckBox::indicator { border-radius: 3px; }
QCheckBox::indicator:checked { background: #36d69a; border-color: #36d69a; }
QRadioButton::indicator { border-radius: 8px; }
QRadioButton::indicator:checked { background: #36d69a; border: 4px solid #17231d; }

QProgressBar {
    background: #182027;
    border: 0;
    border-radius: 3px;
    text-align: center;
    color: #aebbc7;
}
QProgressBar::chunk { background: #36d69a; border-radius: 3px; }

QToolTip {
    background: #182027;
    color: #e6edf3;
    border: 1px solid #35434d;
    padding: 6px 8px;
}
QDialog { background: #10161b; }
QMessageBox { background: #10161b; }
QDialogButtonBox QPushButton { min-width: 72px; }


/* EXVOLT_WORKSPACE_REDESIGN_V1 */

/* Global foundation */
QMainWindow, QWidget {
    color: #dce5ed;
    font-family: "Inter", "Noto Sans", sans-serif;
    font-size: 12px;
}

QMainWindow {
    background: #090d11;
}

QMenuBar {
    background: #0c1117;
    color: #8999a8;
    border-bottom: 1px solid #202a34;
    padding: 5px 8px;
}

QMenuBar::item {
    padding: 7px 12px;
    border-radius: 5px;
}

QMenuBar::item:selected {
    background: #172b25;
    color: #38dda1;
}

QMenu {
    background: #111820;
    border: 1px solid #2a3742;
    padding: 5px;
}

QMenu::item {
    padding: 8px 28px;
    border-radius: 5px;
}

QMenu::item:selected {
    background: #17352a;
    color: #48e6ad;
}

/* New layered workspace surfaces */
QFrame#workspaceHeader {
    background: #10171e;
    border: 1px solid #26323d;
    border-radius: 12px;
}

QFrame#workspaceCard,
QFrame#exvoltPanel {
    background: #10171e;
    border: 1px solid #26323d;
    border-radius: 10px;
}

QFrame#workspaceToolbar {
    background: #0d141a;
    border: 1px solid #25313b;
    border-radius: 8px;
}

QLabel#workspaceTitle {
    color: #edf5fa;
    font-size: 22px;
    font-weight: 800;
}

QLabel#workspaceSubtitle {
    color: #778998;
    font-size: 11px;
}

QLabel#sectionTitle {
    color: #dce8ef;
    font-size: 12px;
    font-weight: 700;
}

QLabel#mutedLabel {
    color: #738595;
}

/* Sidebar */
QWidget#sidebar {
    background: #0b1117;
    border-right: 1px solid #202c36;
}

QLabel#sidebarBrand {
    color: #40e2a6;
    font-size: 23px;
    font-weight: 900;
    letter-spacing: 3px;
}

QLabel#sidebarCaption {
    color: #5f7485;
    font-size: 9px;
    font-weight: 800;
    letter-spacing: 2px;
}

QPushButton#navButton {
    background: transparent;
    color: #8a9baa;
    border: 1px solid transparent;
    border-radius: 7px;
    text-align: left;
    padding: 11px 13px;
    font-weight: 600;
}

QPushButton#navButton:hover {
    background: #131e26;
    color: #dce8ef;
}

QPushButton#navButton:checked,
QPushButton#navButton[active="true"] {
    background: #142b23;
    color: #43e0a4;
    border: 1px solid #214a38;
}

/* Toolbars and actions */
QPushButton {
    background: #17212a;
    color: #aebdca;
    border: 1px solid #2b3945;
    border-radius: 6px;
    padding: 7px 12px;
    min-height: 17px;
}

QPushButton:hover {
    background: #202d37;
    color: #e6f0f6;
    border-color: #405361;
}

QPushButton:pressed {
    background: #13251e;
    border-color: #2e9d72;
}

QPushButton:disabled {
    background: #10161c;
    color: #465562;
    border-color: #202a33;
}

QPushButton#primaryAction,
QPushButton#btn_attack {
    background: #123d2d;
    color: #48e5a9;
    border: 1px solid #237b55;
    font-weight: 700;
}

QPushButton#primaryAction:hover,
QPushButton#btn_attack:hover {
    background: #18533c;
    border-color: #35c98b;
}

QPushButton#dangerAction,
QPushButton#btn_drop {
    background: #25161a;
    color: #e79a9e;
    border: 1px solid #563037;
}

/* Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #0b1218;
    color: #d9e5ed;
    border: 1px solid #2a3742;
    border-radius: 6px;
    padding: 7px 9px;
    selection-background-color: #176747;
    min-height: 18px;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #2a9e71;
    background: #0d151b;
}

QComboBox::drop-down {
    border: 0;
    width: 24px;
}

QComboBox QAbstractItemView {
    background: #111a22;
    color: #dce5ed;
    selection-background-color: #17432f;
    border: 1px solid #2b3945;
}

QCheckBox {
    spacing: 8px;
    color: #9babb9;
}

QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border: 1px solid #354652;
    border-radius: 4px;
    background: #0d141a;
}

QCheckBox::indicator:checked {
    background: #1b8a5d;
    border-color: #39d99b;
}

/* Editors */
QTextEdit, QPlainTextEdit {
    background: #0a1015;
    color: #cbd8e2;
    border: 1px solid #25323d;
    border-radius: 7px;
    padding: 8px;
    selection-background-color: #174c37;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #267d59;
}

/* Tables */
QTableWidget, QTableView {
    background: #0b1218;
    alternate-background-color: #0e161d;
    color: #b9c8d4;
    border: 1px solid #26333e;
    border-radius: 7px;
    gridline-color: #1c2832;
    selection-background-color: #173b2b;
    selection-color: #e5f7ee;
}

QHeaderView::section {
    background: #111a22;
    color: #8194a4;
    border: 0;
    border-bottom: 1px solid #2a3742;
    border-right: 1px solid #202b35;
    padding: 10px 8px;
    font-weight: 700;
}

QTableWidget::item {
    padding: 5px;
    border-bottom: 1px solid #18232c;
}

QTableWidget::item:hover {
    background: #14232b;
}

/* Progress / splitters / scrollbars */
QProgressBar {
    background: #17212a;
    border: 0;
    border-radius: 4px;
    text-align: center;
    color: #8b9eac;
    max-height: 9px;
}

QProgressBar::chunk {
    background: #2dd491;
    border-radius: 4px;
}

QSplitter::handle {
    background: #1c2832;
}

QSplitter::handle:hover {
    background: #2e9b70;
}

QScrollBar:vertical {
    background: #0b1117;
    width: 9px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #293944;
    min-height: 25px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #3b5966;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QStatusBar {
    background: #0b1117;
    color: #728594;
    border-top: 1px solid #202b35;
}

QToolTip {
    background: #17232c;
    color: #e3edf4;
    border: 1px solid #344652;
    padding: 5px;
}



/* EXVOLT_UI_REPLACEMENT_V2 */
QFrame#applicationHeader {
    background: #0d141a;
    border-bottom: 1px solid #26343e;
}
QWidget#applicationShell { background: #090e13; }
QFrame#sidebar {
    background: #0b1218;
    border-right: 1px solid #26313b;
}
QTabWidget#proxySubTabs::pane {
    border: 0;
    background: #090e13;
}
QTabWidget#proxySubTabs QTabBar::tab {
    background: #0d141a;
    color: #8294a3;
    border: 0;
    border-bottom: 2px solid transparent;
    padding: 13px 22px;
    margin-right: 2px;
}
QTabWidget#proxySubTabs QTabBar::tab:selected {
    background: #111c22;
    color: #42dda4;
    border-bottom: 2px solid #2dd491;
}
QPushButton#navButton {
    text-align: left;
    padding: 12px 14px;
    background: transparent;
    color: #8395a4;
    border: 1px solid transparent;
    border-radius: 7px;
    font-weight: 600;
}
QPushButton#navButton:hover {
    background: #142029;
    color: #e1ebf2;
}
QPushButton#navButton:checked {
    background: #142b22;
    color: #43dda5;
    border: 1px solid #24533d;
}
QPushButton#primaryAction {
    background: #15432f;
    color: #49e4ab;
    border: 1px solid #287d56;
    font-weight: 700;
}
QPushButton#dangerAction {
    background: #27171b;
    color: #e69ca3;
    border: 1px solid #59313a;
}

"""

