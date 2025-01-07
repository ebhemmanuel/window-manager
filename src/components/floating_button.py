from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen, QApplication

class FloatingActionButton(QWidget):
    """Material Design-style floating action button."""
    
    clicked = pyqtSignal()  # Signal emitted when button is clicked
    
    def __init__(self, size: int = 56, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # State tracking
        self.is_pressed = False
        self.drag_start = None
        self.hover = False
        
        # Setup shadow effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(0, 2)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(self.shadow)
        
        # Setup hover animation
        self.hover_animation = QPropertyAnimation(self, b"size")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Colors
        self.base_color = QColor(65, 65, 65)
        self.hover_color = QColor(75, 75, 75)
        self.press_color = QColor(55, 55, 55)
        self.icon_color = QColor(255, 255, 255)
    
    def paintEvent(self, event):
        """Draw the button and its icon."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw circular background
        path = QPainterPath()
        rect = self.rect().adjusted(4, 4, -4, -4)  # Add padding
        path.addEllipse(rect)
        
        # Determine background color based on state
        if self.is_pressed:
            bg_color = self.press_color
        elif self.hover:
            bg_color = self.hover_color
        else:
            bg_color = self.base_color
            
        painter.fillPath(path, bg_color)
        
        # Draw grid icon
        painter.setPen(QPen(self.icon_color, 2))
        center = rect.center()
        icon_size = self.width() * 0.4  # 40% of button size
        
        # Draw grid dots
        dot_spacing = icon_size / 2
        for i in range(3):
            for j in range(3):
                x = center.x() - icon_size/2 + i * dot_spacing
                y = center.y() - icon_size/2 + j * dot_spacing
                painter.drawPoint(int(x), int(y))
    
    def enterEvent(self, event):
        """Handle mouse enter event."""
        self.hover = True
        self.hover_animation.setStartValue(self.size())
        self.hover_animation.setEndValue(self.size() + QSize(4, 4))
        self.hover_animation.start()
        self.update()
    
    def leaveEvent(self, event):
        """Handle mouse leave event."""
        self.hover = False
        self.hover_animation.setStartValue(self.size())
        self.hover_animation.setEndValue(QSize(56, 56))
        self.hover_animation.start()
        self.update()
    
    def mousePressEvent(self, event):
        """Handle mouse press for click and drag."""
        if event.button() == Qt.LeftButton:
            self.is_pressed = True
            self.drag_start = event.globalPos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release for click and drag."""
        if event.button() == Qt.LeftButton:
            self.is_pressed = False
            if self.rect().contains(event.pos()):
                self.clicked.emit()
            self.drag_start = None
            self.update()
    
    def mouseMoveEvent(self, event):
        """Handle dragging the button."""
        if self.drag_start:
            delta = event.globalPos() - self.drag_start
            new_pos = self.pos() + delta
            
            # Keep button within screen bounds
            screen = QApplication.primaryScreen().geometry()
            new_pos.setX(max(0, min(new_pos.x(), 
                                  screen.width() - self.width())))
            new_pos.setY(max(0, min(new_pos.y(), 
                                  screen.height() - self.height())))
            
            self.move(new_pos)
            self.drag_start = event.globalPos()
    
    def set_colors(self, base: str = None, hover: str = None, 
                  press: str = None, icon: str = None):
        """Update button colors."""
        if base:
            self.base_color = QColor(base)
        if hover:
            self.hover_color = QColor(hover)
        if press:
            self.press_color = QColor(press)
        if icon:
            self.icon_color = QColor(icon)
        self.update()