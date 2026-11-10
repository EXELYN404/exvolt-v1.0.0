from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QSplitter
from PyQt5.QtCore import Qt
from ui.components import DarkEditor, DarkCard, StatusBadge
from ui.design_tokens import *

class DecoderPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        
        # Header section
        header = QHBoxLayout()
        header.addWidget(DarkCard("Operations", border_color=teal_muted))
        self.layout().addLayout(header)
        
        # Split editor area
        splitter = QSplitter(Qt.Horizontal)
        
        # Input editor
        input_layout = QVBoxLayout()
        input_layout.addWidget(DarkCard("Input", border_color=teal_muted))
        input_editor = DarkEditor()
        input_editor.setPlaceholderText("Enter data to decode...")
        input_layout.addWidget(input_editor)
        
        # Operation buttons
        op_layout = QHBoxLayout()
        operations = [
            ("URL Encode", "url_encode"),
            ("URL Decode", "url_decode"),
            ("Base64 Encode", "base64_encode"),
            ("Base64 Decode", "base64_decode"),
            ("HTML Encode", "html_encode"),
            ("HTML Decode", "html_decode"),
            ("Hex Encode", "hex_encode"),
            ("Hex Decode", "hex_decode")
        ]
        
        for btn_text, action in operations:
            btn = QPushButton(btn_text)
            btn.setStyleSheet(secondary_button_style)
            btn.clicked.connect(lambda checked, a=action: self.operation_clicked(a))
            op_layout.addWidget(btn)
            
        input_layout.addLayout(op_layout)
        input_card = DarkCard("Input Operations", border_color=teal_muted)
        input_card.setLayout(input_layout)
        splitter.addWidget(input_card)
        
        # Output editor
        output_layout = QVBoxLayout()
        output_layout.addWidget(DarkCard("Output", border_color=teal_muted))
        output_editor = DarkEditor()
        output_editor.setPlaceholderText("Decoded result will appear here...")
        output_layout.addWidget(output_editor)
        output_card = DarkCard("Output Operations", border_color=teal_muted)
        output_card.setLayout(output_layout)
        splitter.addWidget(output_card)
        
        self.layout().addWidget(splitter)
        
        # Control panel
        control_layout = QHBoxLayout()
        copy_btn = QPushButton("Copy Output")
        copy_btn.setStyleSheet(secondary_button_style)
        clear_input_btn = QPushButton("Clear Input")
        clear_input_btn.setStyleSheet(danger_button_style)
        clear_output_btn = QPushButton("Clear Output")
        clear_output_btn.setStyleSheet(danger_button_style)
        
        control_layout.addWidget(copy_btn)
        control_layout.addWidget(clear_input_btn)
        control_layout.addWidget(clear_output_btn)
        
        self.layout().addLayout(control_layout)
        
        # Status bar
        self.status = StatusBadge("Idle", text_color=text_secondary)
        self.layout().addWidget(self.status)
        
        # Connect signals
        copy_btn.clicked.connect(self.copy_output)
        clear_input_btn.clicked.connect(self.clear_input)
        clear_output_btn.clicked.connect(self.clear_output)
        
    def operation_clicked(self, action):
        # Implementation would connect to backend
        pass
        
    def copy_output(self):
        # Implementation would connect to backend
        pass
        
    def clear_input(self):
        # Implementation would connect to backend
        pass
        
    def clear_output(self):
        # Implementation would connect to backend
        pass