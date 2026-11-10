from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QSplitter
from PyQt5.QtCore import Qt
from ui.components import DarkEditor, DarkCard, MetricCard, StatusBadge
from ui.design_tokens import *

class ComparerPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        
        # Header section
        header = QHBoxLayout()
        header.addWidget(DarkCard("Left Request", border_color=teal_muted))
        header.addSpacing(16)
        header.addWidget(DarkCard("Right Request", border_color=teal_muted))
        self.layout().addLayout(header)
        
        # Split editor area
        splitter = QSplitter(Qt.Horizontal)
        
        # Left request editor
        left_editor = DarkEditor()
        left_editor.setPlaceholderText("Enter first HTTP request here...")
        splitter.addWidget(left_editor)
        
        # Right request editor
        right_editor = DarkEditor()
        right_editor.setPlaceholderText("Enter second HTTP request here...")
        splitter.addWidget(right_editor)
        
        self.layout().addWidget(splitter)
        
        # Control panel
        control_layout = QHBoxLayout()
        control_layout.addWidget(DarkCard("Comparison Options", border_color=teal_muted))
        compare_btn = QPushButton("Compare")
        compare_btn.setStyleSheet(primary_button_style)
        control_layout.addWidget(compare_btn)
        
        diff_btn = QPushButton("Show Differences")
        diff_btn.setStyleSheet(secondary_button_style)
        control_layout.addWidget(diff_btn)
        
        self.layout().addLayout(control_layout)
        
        # Status bar
        self.status = StatusBadge("Idle", text_color=text_secondary)
        self.layout().addWidget(self.status)
        
        # Connect signals
        compare_btn.clicked.connect(self.compare_requests)
        diff_btn.clicked.connect(self.show_differences)
        
    def compare_requests(self):
        # Implementation would connect to backend
        pass
        
    def show_differences(self):
        # Implementation would connect to backend
        pass