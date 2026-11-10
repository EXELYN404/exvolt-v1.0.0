from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton
from PyQt5.QtCore import Qt
from ui.components import DarkCard, StatusBadge
from ui.design_tokens import *

class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        
        # Header section
        header = QHBoxLayout()
        header.addWidget(DarkCard("EXVOLT", border_color=teal_muted, title_align=Qt.AlignCenter))
        header.addSpacing(16)
        header.addWidget(DarkCard("Version 1.0.0", border_color=teal_muted))
        self.layout().addLayout(header)
        
        # About content
        about_layout = QVBoxLayout()
        
        about_layout.addWidget(DarkCard("Application Description", border_color=teal_muted))
        description = QTextEdit()
        description.setReadOnly(True)
        description.setPlaceholderText("EXVOLT is a premium cybersecurity desktop application designed for professional security analysis and penetration testing. Built with Python and PyQt5, it provides a modern dark glassmorphism interface with neon teal accents.")
        about_layout.addWidget(description)
        
        about_layout.addWidget(DarkCard("Key Features", border_color=teal_muted))
        features = QTextEdit()
        features.setReadOnly(True)
        features.setPlaceholderText("• Proxy/Intercept\n• Repeater/Intruder\n• Comparer/Sequencer\n• WebSocket Analyzer\n• Decoder/History\n• SOC Dashboard Visualization")
        about_layout.addWidget(features)
        
        about_layout.addWidget(DarkCard("Version Information", border_color=teal_muted))
        version_info = QTextEdit()
        version_info.setReadOnly(True)
        version_info.setPlaceholderText("Version: 1.0.0\nBuilt: 2026\nEXVOLT Security Solutions")
        about_layout.addWidget(version_info)
        
        self.layout().addLayout(about_layout)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(DarkCard("EXVOLT Security Solutions", border_color=teal_muted))
        footer_layout.addStretch()
        self.layout().addLayout(footer_layout)
        
        # Status bar
        self.status = StatusBadge("Idle", text_color=text_secondary)
        self.layout().addWidget(self.status)