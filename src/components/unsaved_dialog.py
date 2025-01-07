from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QFont

class UnsavedDialog(QDialog):
    """Modern dialog for handling unsaved changes."""
    
    confirmed = pyqtSignal(bool)  # Signal emitted with user's decision
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        
        # Setup fade effect
        self.fade_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.fade_effect)
        
        self.fade_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Unsaved Changes")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title)
        
        # Message
        message = QLabel(
            "You have unsaved changes in the current layout.\n"
            "Would you like to save them before continuing?"
        )
        message.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
            }
        """)
        layout.addWidget(message)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        save_btn.clicked.connect(lambda: self.handle_decision(True))
        
        discard_btn = QPushButton("Discard")
        discard_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ff5252;
                border: 1px solid #ff5252;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 82, 82, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 82, 82, 0.2);
            }
        """)
        discard_btn.clicked.connect(lambda: self.handle_decision(False))
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(discard_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def handle_decision(self, save: bool):
        """Handle user's decision."""
        self.confirmed.emit(save)
        self.accept()
    
    def showEvent(self, event):
        """Show dialog with fade in animation."""
        super().showEvent(event)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()
    
    def closeEvent(self, event):
        """Close dialog with fade out animation."""
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()
        event.ignore()
    
    def paintEvent(self, event):
        """Draw the dialog background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw semi-transparent backdrop
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))
        
        # Draw dialog background
        path = QPainterPath()
        content_rect = self.rect().adjusted(
            self.width()//4, self.height()//4,
            -self.width()//4, -self.height()//4
        )
        path.addRoundedRect(content_rect, 12, 12)
        
        # Draw shadow
        shadow_color = QColor(0, 0, 0, 50)
        for i in range(10):
            painter.setPen(Qt.NoPen)
            painter.setBrush(shadow_color)
            shadow_path = QPainterPath()
            shadow_path.addRoundedRect(
                content_rect.adjusted(-i, -i, i, i), 
                12, 12
            )
            painter.drawPath(shadow_path)
            shadow_color.setAlpha(max(0, shadow_color.alpha() - 5))
        
        # Draw main background
        painter.fillPath(path, QColor(42, 42, 42))