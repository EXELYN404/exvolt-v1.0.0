from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QComboBox, QSplitter
from PyQt5.QtCore import Qt
from ui.components import DarkEditor, DarkCard, MetricCard, StatusBadge
from ui.design_tokens import *

class IntruderPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        
        # Header section
        header = QHBoxLayout()
        header.addWidget(DarkCard("Request Editor", border_color=teal_muted))
        header.addSpacing(16)
        header.addWidget(DarkCard("Payload Configuration", border_color=teal_muted))
        self.layout().addLayout(header)
        
        # Split editor area
        splitter = QSplitter(Qt.Horizontal)
        
        # Request editor
        request_editor = DarkEditor()
        request_editor.setPlaceholderText("Enter HTTP request here...")
        splitter.addWidget(request_editor)
        
        # Payload configuration
        payload_layout = QVBoxLayout()
        
        # Payload set selector
        payload_layout.addWidget(DarkCard("Payload Set", border_color=teal_muted))
        payload_combo = QComboBox()
        payload_combo.addItems(["Wordlist", "Custom", "File", "Random"])
        payload_layout.addWidget(payload_combo)
        
        # Thread count
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("Threads:"))
        thread_spin = QSpinBox()
        thread_spin.setRange(1, 100)
        thread_spin.setValue(10)
        thread_layout.addWidget(thread_spin)
        payload_layout.addLayout(thread_layout)
        
        # Timeout
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Timeout (ms):"))
        timeout_spin = QSpinBox()
        timeout_spin.setRange(100, 60000)
        timeout_spin.setValue(5000)
        timeout_layout.addWidget(timeout_spin)
        payload_layout.addLayout(timeout_layout)
        
        # Grep expression
        grep_layout = QHBoxLayout()
        grep_layout.addWidget(QLabel("Grep:"))
        grep_input = QTextEdit()
        grep_input.setPlaceholderText("Enter grep expression...")
        grep_layout.addWidget(grep_input)
        payload_layout.addLayout(grep_layout)
        
        payload_card = DarkCard("Payload Configuration", border_color=teal_muted)
        payload_card.setLayout(payload_layout)
        splitter.addWidget(payload_card)
        
        self.layout().addWidget(splitter)
        
        # Control panel
        control_layout = QHBoxLayout()
        start_btn = QPushButton("Start Attack")
        start_btn.setStyleSheet(primary_button_style)
        control_layout.addWidget(start_btn)
        
        stop_btn = QPushButton("Stop")
        stop_btn.setStyleSheet(danger_button_style)
        control_layout.addWidget(stop_btn)
        
        progress_btn = QPushButton("Progress")
        progress_btn.setStyleSheet(secondary_button_style)
        control_layout.addWidget(progress_btn)
        
        self.layout().addLayout(control_layout)
        
        # Status bar
        self.status = StatusBadge("Idle", text_color=text_secondary)
        self.layout().addWidget(self.status)
        
        # Connect signals
        start_btn.clicked.connect(self.start_attack)
        stop_btn.clicked.connect(self.stop_attack)
        progress_btn.clicked.connect(self.show_progress)
        
    def start_attack(self):
        # Implementation would connect to backend
        pass
        
    def stop_attack(self):
        # Implementation would connect to backend
        pass
        
    def show_progress(self):
        # Implementation would connect to backend
        pass