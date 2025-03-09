from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen, QFont

class LayoutStatusIndicator(QWidget):
    """Visual indicator for layout status (temporary/saved)."""
    
    clicked = pyqtSignal()  # Emitted when indicator is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # State
        self.is_temporary = False
        self.has_changes = False
        self.is_animating = False
        
        # Colors
        self.temp_color = QColor("#FFA500")  # Orange for temporary
        self.saved_color = QColor("#4CAF50")  # Green for saved
        self.modified_color = QColor("#FF5252")  # Red for unsaved changes
        
        # Setup animations
        self.setup_animations()
    
    def setup_animations(self):
        """Setup pulse animation for unsaved changes."""
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.pulse_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setLoopCount(-1)  # Infinite
        self.pulse_animation.setStartValue(1.0)
        self.pulse_animation.setEndValue(0.5)
        self.pulse_animation.setEasingCurve(QEasingCurve.InOutQuad)
    
    def set_temporary(self, is_temp: bool):
        """Set temporary status."""
        if self.is_temporary != is_temp:
            self.is_temporary = is_temp
            self.update()
    
    def set_has_changes(self, has_changes: bool):
        """Set unsaved changes status."""
        if self.has_changes != has_changes:
            self.has_changes = has_changes
            
            # Start/stop pulse animation
            if has_changes and not self.pulse_animation.state():
                self.pulse_animation.start()
            elif not has_changes and self.pulse_animation.state():
                self.pulse_animation.stop()
                self.opacity_effect.setOpacity(1.0)
            
            self.update()
    
    def paintEvent(self, event):
        """Draw the status indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Determine color based on state
        if self.has_changes:
            color = self.modified_color
        elif self.is_temporary:
            color = self.temp_color
        else:
            color = self.saved_color
        
        # Draw circle background
        path = QPainterPath()
        path.addEllipse(2, 2, 20, 20)
        
        painter.fillPath(path, color)
        
        # Draw icon based on state
        painter.setPen(QPen(Qt.white, 2))
        if self.has_changes:
            # Draw dot
            painter.drawEllipse(10, 10, 4, 4)
        elif self.is_temporary:
            # Draw T
            painter.setFont(QFont("Arial", 12, QFont.Bold))
            painter.drawText(rect(), Qt.AlignCenter, "T")
        else:
            # Draw checkmark
            painter.drawLine(7, 12, 10, 15)
            painter.drawLine(10, 15, 17, 8)
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
    
    def enterEvent(self, event):
        """Handle mouse enter."""
        if not self.has_changes:
            self.setCursor(Qt.PointingHandCursor)
    
    def leaveEvent(self, event):
        """Handle mouse leave."""
        self.unsetCursor()
    
    def get_tooltip_text(self) -> str:
        """Get appropriate tooltip text based on state."""
        if self.has_changes:
            return "Unsaved changes"
        elif self.is_temporary:
            return "Temporary layout"
        return "Saved layout"