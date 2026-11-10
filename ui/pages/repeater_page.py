from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QComboBox, QSplitter
from PyQt5.QtCore import Qt
from ui.components import DarkEditor, DarkCard, MetricCard, StatusBadge
from ui.design_tokens import *

class RepeaterPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        
        # Header section
        header = QHBoxLayout()
        header.addWidget(DarkCard("Request Editor", border_color=teal_muted))
        header.addSpacing(16)
        header.addWidget(DarkCard("Response Viewer", border_color=teal_muted))
        self.layout().addLayout(header)
        
        # Split editor area
        splitter = QSplitter(Qt.Horizontal)
        
        # Request editor
        request_editor = DarkEditor()
        request_editor.setPlaceholderText("Enter HTTP request here...")
        splitter.addWidget(request_editor)
        
        # Response viewer
        response_viewer = DarkEditor()
        response_viewer.setPlaceholderText("Response will appear here...")
        splitter.addWidget(response_viewer)
        
        self.layout().addWidget(splitter)
        
        # Control panel
        control_layout = QHBoxLayout()
        control_layout.addWidget(DarkCard("Request Metadata", border_color=teal_muted))
        control_layout.addWidget(QLabel("Method:"))
        method_combo = QComboBox()
        method_combo.addItems(["GET", "POST", "PUT", "DELETE", "HEAD", "PATCH"])
        control_layout.addWidget(method_combo)
        
        control_layout.addWidget(QLabel("URL:"))
        url_input = QTextEdit()
        url_input.setPlaceholderText("http://example.com/api/endpoint")
        control_layout.addWidget(url_input)
        
        send_btn = QPushButton("Send")
        send_btn.setStyleSheet(primary_button_style)
        control_layout.addWidget(send_btn)
        
        status_btn = StatusBadge("Ready", success_color)
        control_layout.addWidget(status_btn)
        
        self.layout().addLayout(control_layout)
        
        # Status bar
        self.status = StatusBadge("Idle", text_color=text_secondary)
        self.layout().addWidget(self.status)
        
        # Connect signals
        send_btn.clicked.connect(self.send_request)
        
    def send_request(self):
        # Implementation would connect to backend
        pass