from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QLabel, QSplitter
from PyQt5.QtCore import Qt
from ui.components import DarkTable, DarkCard, StatusBadge
from ui.design_tokens import *

class WebSocketPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        
        # Header section
        header = QHBoxLayout()
        header.addWidget(DarkCard("Traffic Table", border_color=teal_muted))
        header.addSpacing(16)
        header.addWidget(DarkCard("Search & Filters", border_color=teal_muted))
        self.layout().addLayout(header)
        
        # Split layout
        splitter = QSplitter(Qt.Vertical)
        
        # Traffic table
        traffic_table = DarkTable()
        traffic_table.setColumnCount(5)
        traffic_table.setHorizontalHeaderLabels(["Direction", "Frame Count", "Size", "Timestamp", "Details"])
        splitter.addWidget(traffic_table)
        
        # Search and filters
        filter_layout = QHBoxLayout()
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("Search frames...")
        filter_layout.addWidget(search_input)
        
        direction_filter = QComboBox()
        direction_filter.addItems(["All", "Client to Server", "Server to Client"])
        filter_layout.addWidget(direction_filter)
        
        frame_count_filter = QSpinBox()
        frame_count_filter.setRange(0, 10000)
        frame_count_filter.setValue(100)
        filter_layout.addWidget(QLabel("Max Frames:"))
        filter_layout.addWidget(frame_count_filter)
        
        filter_card = DarkCard("Search & Filters", border_color=teal_muted)
        filter_card.setLayout(filter_layout)
        splitter.addWidget(filter_card)
        
        self.layout().addWidget(splitter)
        
        # Control panel
        control_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear Traffic")
        clear_btn.setStyleSheet(danger_button_style)
        control_layout.addWidget(clear_btn)
        
        self.layout().addLayout(control_layout)
        
        # Status bar
        self.status = StatusBadge("Idle", text_color=text_secondary)
        self.layout().addWidget(self.status)
        
        # Connect signals
        clear_btn.clicked.connect(self.clear_traffic)
        
    def clear_traffic(self):
        # Implementation would connect to backend
        pass