from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath

class PreviewRect(QWidget):
    """Animated preview rectangle for window placement."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.target_rect = QRect()
        self.color = QColor("#FFA500")  # Default orange
        self.opacity = 0.3
        self.border_width = 2
        self.corner_radius = 8
        
        # Setup fade animation
        self.fade_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.fade_effect)
        
        self.fade_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Setup position/size animation
        self.geometry_animation = QPropertyAnimation(self, b"geometry")
        self.geometry_animation.setDuration(150)
        self.geometry_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def set_rect(self, rect: QRect, animate: bool = True):
        """Update the preview rectangle with optional animation."""
        if animate and self.isVisible():
            self.geometry_animation.setStartValue(self.geometry())
            self.geometry_animation.setEndValue(rect)
            self.geometry_animation.start()
        else:
            self.setGeometry(rect)
        
        self.target_rect = rect
        self.update()
    
    def show_preview(self):
        """Show the preview with fade in animation."""
        self.fade_animation.stop()
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(self.opacity)
        self.show()
        self.fade_animation.start()
    
    def hide_preview(self):
        """Hide the preview with fade out animation."""
        self.fade_animation.stop()
        self.fade_animation.setStartValue(self.opacity)
        self.fade_animation.setEndValue(0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()
    
    def set_color(self, color: QColor):
        """Set the preview color."""
        self.color = color
        self.update()
    
    def set_opacity(self, opacity: float):
        """Set the preview opacity."""
        self.opacity = max(0.0, min(1.0, opacity))
        if self.isVisible():
            self.fade_effect.setOpacity(self.opacity)
    
    def paintEvent(self, event):
        """Draw the preview rectangle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create rounded rectangle path
        path = QPainterPath()
        path.addRoundedRect(
            self.rect().adjusted(
                self.border_width/2,
                self.border_width/2,
                -self.border_width/2,
                -self.border_width/2
            ),
            self.corner_radius,
            self.corner_radius
        )
        
        # Draw semi-transparent fill
        fill_color = QColor(self.color)
        fill_color.setAlpha(int(40 * self.opacity))
        painter.fillPath(path, fill_color)
        
        # Draw border
        pen = QPen(self.color)
        pen.setWidth(self.border_width)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Draw corner indicators
        corner_size = 16
        corner_color = QColor(self.color)
        corner_color.setAlpha(int(255 * self.opacity))
        pen.setColor(corner_color)
        painter.setPen(pen)
        
        # Top-left corner
        painter.drawLine(0, corner_size, 0, 0)
        painter.drawLine(0, 0, corner_size, 0)
        
        # Top-right corner
        painter.drawLine(self.width() - corner_size, 0, self.width(), 0)
        painter.drawLine(self.width(), 0, self.width(), corner_size)
        
        # Bottom-left corner
        painter.drawLine(0, self.height() - corner_size, 0, self.height())
        painter.drawLine(0, self.height(), corner_size, self.height())
        
        # Bottom-right corner
        painter.drawLine(self.width() - corner_size, self.height(), 
                        self.width(), self.height())
        painter.drawLine(self.width(), self.height() - corner_size,
                        self.width(), self.height())