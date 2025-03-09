from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect, QApplication
from PyQt5.QtCore import QRectF, Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen, QFont

class FloatingActionButton(QWidget):
    """Material Design-style floating action button."""

    clicked = pyqtSignal()  # Signal emitted when button is clicked
    moved = pyqtSignal(QPoint)  # Signal emitted when button position changes
    
    def __init__(self, size: int = 56, text: str = None, parent=None, icon_color: str = "#FFFFFF"):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # State tracking
        self.is_pressed = False
        self.drag_start = None
        self.hover = False
        self.text = text
        self.font = QFont("Arial", 14, QFont.Bold)

        # Setup shadow effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(0, 2)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(self.shadow)

        # Colors
        self.base_color = QColor(65, 65, 65)
        self.hover_color = QColor(75, 75, 75)
        self.press_color = QColor(55, 55, 55)
        self.icon_color = QColor(icon_color)
        self.text_color = QColor(255, 255, 255)

        # Setup hover animation
        self.hover_animation = QPropertyAnimation(self, b"size")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)

        # Position animation
        self.move_animation = QPropertyAnimation(self, b"geometry")
        self.move_animation.setDuration(300)
        self.move_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.move_animation.finished.connect(self._on_move_finished)

    def paintEvent(self, event):
        """Draw the button and its text/icon."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw circular background
        path = QPainterPath()
        rect = self.rect().adjusted(4, 4, -4, -4)  # Add padding
        path.addEllipse(QRectF(rect))  # Convert QRect to QRectF

        if self.is_pressed:
            painter.fillPath(path, self.press_color)
        else:
            painter.fillPath(path, self.hover_color if self.underMouse() else self.base_color)

        # Draw text/icon
        if self.text:
            painter.setFont(self.font)
            painter.setPen(QPen(self.text_color))
            painter.drawText(self.rect(), Qt.AlignCenter, self.text)
        else:
            # Default grid dots as icon
            center = rect.center()
            icon_size = self.width() * 0.4  # 40% of button size

            # Draw grid dots
            dot_spacing = icon_size / 2
            for i in range(3):
                for j in range(3):
                    x = center.x() - icon_size / 2 + i * dot_spacing
                    y = center.y() - icon_size / 2 + j * dot_spacing
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
        self.hover_animation.setEndValue(QSize(self.width(), self.height()))
        self.hover_animation.start()
        self.update()

    def mousePressEvent(self, event):
        """Handle mouse press for click and drag."""
        if event.button() == Qt.LeftButton:
            self.is_pressed = True
            self.drag_start = event.globalPos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release for click."""
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
            new_pos.setX(max(0, min(new_pos.x(), screen.width() - self.width())))
            new_pos.setY(max(0, min(new_pos.y(), screen.height() - self.height())))

            self.move(new_pos)
            self.drag_start = event.globalPos()
            
            # Emit moved signal with new position
            self.moved.emit(new_pos)

    def moveEvent(self, event):
        """Handle any movement of the button."""
        super().moveEvent(event)
        # Only emit moved signal if it's not from an animation
        if not self.move_animation.state() == QPropertyAnimation.Running:
            self.moved.emit(event.pos())

    def set_colors(self, base: str = None, hover: str = None, press: str = None, text: str = None):
        """Update button colors."""
        if base:
            self.base_color = QColor(base)
        if hover:
            self.hover_color = QColor(hover)
        if press:
            self.press_color = QColor(press)
        if text:
            self.text_color = QColor(text)
        self.update()

    def set_text(self, text: str):
        """Set the button's text."""
        self.text = text
        self.update()

    def move_with_animation(self, target_x: int, target_y: int):
        """Move the button to a target position with animation."""
        self.move_animation.setStartValue(self.geometry())
        self.move_animation.setEndValue(QRect(target_x, target_y, self.width(), self.height()))
        self.move_animation.start()

    def _on_move_finished(self):
        """Handle completion of move animation."""
        # Emit moved signal with final position
        self.moved.emit(self.pos())