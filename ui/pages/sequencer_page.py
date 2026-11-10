from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QComboBox, QSplitter
from PyQt5.QtCore import Qt
from ui.components import DarkEditor, DarkCard, MetricCard, StatusBadge
from ui.design_tokens import *

class SequencerPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        
        # Header section
        header = QHBoxLayout()
        header.addWidget(DarkCard("Manual Analysis", border_color=teal_muted))
        header.addSpacing(16)
        header.addWidget(DarkCard("Automatic Collection", border_color=teal_muted))
        self.layout().addLayout(header)
        
        # Split editor area
        splitter = QSplitter(Qt.Horizontal)
        
        # Manual token analysis
        manual_layout = QVBoxLayout()
        manual_layout.addWidget(DarkCard("Token Input", border_color=teal_muted))
        token_input = QTextEdit()
        token_input.setPlaceholderText("Enter tokens to analyze...")
        manual_layout.addWidget(token_input)
        
        # Regex configuration
        regex_layout = QHBoxLayout()
        regex_layout.addWidget(QLabel("Regex:"))
        regex_input = QTextEdit()
        regex_input.setPlaceholderText("Enter regex pattern...")
        regex_layout.addWidget(regex_input)
        manual_layout.addLayout(regex_layout)
        
        manual_card = DarkCard("Manual Analysis", border_color=teal_muted)
        manual_card.setLayout(manual_layout)
        splitter.addWidget(manual_card)
        
        # Automatic collection
        auto_layout = QVBoxLayout()
        auto_layout.addWidget(DarkCard("Collection Source", border_color=teal_muted))
        source_combo = QComboBox()
        source_combo.addItems(["Manual", "URL", "File", "Live Traffic"])
        auto_layout.addWidget(source_combo)
        
        collection_btn = QPushButton("Start Collection")
        collection_btn.setStyleSheet(primary_button_style)
        auto_layout.addWidget(collection_btn)
        
        auto_card = DarkCard("Automatic Collection", border_color=teal_muted)
        auto_card.setLayout(auto_layout)
        splitter.addWidget(auto_card)
        
        self.layout().addWidget(splitter)
        
        # Control panel
        control_layout = QHBoxLayout()
        collect_btn = QPushButton("Collect Tokens")
        collect_btn.setStyleSheet(primary_button_style)
        control_layout.addWidget(collect_btn)
        
        analyze_btn = QPushButton("Analyze")
        analyze_btn.setStyleSheet(secondary_button_style)
        control_layout.addWidget(analyze_btn)
        
        self.layout().addLayout(control_layout)
        
        # Status bar
        self.status = StatusBadge("Idle", text_color=text_secondary)
        self.layout().addWidget(self.status)
        
        # Connect signals
        collect_btn.clicked.connect(self.collect_tokens)
        analyze_btn.clicked.connect(self.analyze_tokens)
        
    def collect_tokens(self):
        # Implementation would connect to backend
        pass
        
    def analyze_tokens(self):
        # Implementation would connect to backend
        pass