from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen
from typing import Dict
from core.ultrawide_grid import JustifyType

class JustifyControls(QWidget):
    """Floating controls for window justification."""
    
    justify_changed = pyqtSignal(JustifyType)  # Emitted when justification changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Control state
        self.current_justify = JustifyType.START
        self.hover_button = None
        self.button_size = 40
        self.spacing = 10
        
        # Set fixed size based on layout
        total_width = (self.button_size * 3) + (self.spacing * 2)
        total_height = (self.button_size * 2) + self.spacing
        self.setFixedSize(total_width, total_height)
        
        # Setup animation
        self.fade_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.fade_effect)
        
        self.fade_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_animation.setDuration(150)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Define button layouts
        self.buttons = {
            JustifyType.START: (0, 0),
            JustifyType.CENTER: (self.button_size + self.spacing, 0),
            JustifyType.END: ((self.button_size + self.spacing) * 2, 0),
            JustifyType.SPACE_BETWEEN: (0, self.button_size + self.spacing),
            JustifyType.SPACE_AROUND: (self.button_size + self.spacing, self.button_size + self.spacing),
            JustifyType.SPACE_EVENLY: ((self.button_size + self.spacing) * 2, self.button_size + self.spacing)
        }
        
        # Colors
        self.base_color = QColor(65, 65, 65)
        self.hover_color = QColor(75, 75, 75)
        self.active_color = QColor("#4CAF50")
        self.icon_color = QColor(255, 255, 255)
    
    def show_controls(self):
        """Show controls with fade animation."""
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.show()
        self.raise_()
        self.fade_animation.start()
    
    def hide_controls(self):
        """Hide controls with fade animation."""
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()
    
    def paintEvent(self, event):
        """Draw the justification controls."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for justify_type, pos in self.buttons.items():
            rect = QRect(pos[0], pos[1], self.button_size, self.button_size)
            
            # Draw button background
            path = QPainterPath()
            path.addRoundedRect(rect, 8, 8)
            
            if justify_type == self.current_justify:
                painter.fillPath(path, self.active_color)
            elif justify_type == self.hover_button:
                painter.fillPath(path, self.hover_color)
            else:
                painter.fillPath(path, self.base_color)
            
            # Draw justify icon
            self._draw_justify_icon(painter, justify_type, rect)
    
    def _draw_justify_icon(self, painter: QPainter, justify_type: JustifyType, rect: QRect):
        """Draw the icon for each justification type."""
        painter.setPen(QPen(self.icon_color, 2))
        
        # Calculate icon bounds
        icon_margin = 8
        icon_rect = rect.adjusted(icon_margin, icon_margin, -icon_margin, -icon_margin)
        center_y = icon_rect.center().y()
        
        if justify_type == JustifyType.START:
            self._draw_start_icon(painter, icon_rect)
        elif justify_type == JustifyType.CENTER:
            self._draw_center_icon(painter, icon_rect)
        elif justify_type == JustifyType.END:
            self._draw_end_icon(painter, icon_rect)
        elif justify_type == JustifyType.SPACE_BETWEEN:
            self._draw_space_between_icon(painter, icon_rect)
        elif justify_type == JustifyType.SPACE_AROUND:
            self._draw_space_around_icon(painter, icon_rect)
        elif justify_type == JustifyType.SPACE_EVENLY:
            self._draw_space_evenly_icon(painter, icon_rect)
    
    def _draw_start_icon(self, painter: QPainter, rect: QRect):
        """Draw start justification icon."""
        painter.drawLine(rect.left(), rect.center().y(), rect.center().x(), rect.center().y())
        self._draw_arrow(painter, QPoint(rect.left(), rect.center().y()), 6, 0)
    
    def _draw_center_icon(self, painter: QPainter, rect: QRect):
        """Draw center justification icon."""
        center = rect.center()
        painter.drawLine(center.x() - 8, center.y(), center.x() + 8, center.y())
        self._draw_arrow(painter, QPoint(center.x() - 8, center.y()), 6, 180)
        self._draw_arrow(painter, QPoint(center.x() + 8, center.y()), 6, 0)
    
    def _draw_end_icon(self, painter: QPainter, rect: QRect):
        """Draw end justification icon."""
        painter.drawLine(rect.center().x(), rect.center().y(), rect.right(), rect.center().y())
        self._draw_arrow(painter, QPoint(rect.right(), rect.center().y()), 6, 180)
    
    def _draw_space_between_icon(self, painter: QPainter, rect: QRect):
        """Draw space-between justification icon."""
        y = rect.center().y()
        x1 = rect.left() + 4
        x2 = rect.right() - 4
        
        painter.drawLine(x1, y, x2, y)
        painter.drawLine(rect.center().x(), y - 4, rect.center().x(), y + 4)
    
    def _draw_space_around_icon(self, painter: QPainter, rect: QRect):
        """Draw space-around justification icon."""
        y = rect.center().y()
        margin = 6
        
        painter.drawLine(rect.left() + margin, y, rect.right() - margin, y)
        for x in [rect.left() + margin, rect.center().x(), rect.right() - margin]:
            painter.drawLine(x, y - 4, x, y + 4)
    
    def _draw_space_evenly_icon(self, painter: QPainter, rect: QRect):
        """Draw space-evenly justification icon."""
        y = rect.center().y()
        step = rect.width() / 4
        
        for i in range(4):
            x = rect.left() + (step * i)
            painter.drawLine(int(x), y - 4, int(x), y + 4)
        painter.drawLine(rect.left(), y, rect.right(), y)
    
    def _draw_arrow(self, painter: QPainter, point: QPoint, size: int, angle: float):
        """Draw an arrow for directional indicators."""
        path = QPainterPath()
        if angle == 0:  # Right arrow
            path.moveTo(point)
            path.lineTo(point + QPoint(size, -size/2))
            path.lineTo(point + QPoint(size, size/2))
        else:  # Left arrow
            path.moveTo(point)
            path.lineTo(point - QPoint(size, -size/2))
            path.lineTo(point - QPoint(size, size/2))
        path.closeSubpath()
        painter.fillPath(path, self.icon_color)
    
    def mousePressEvent(self, event):
        """Handle mouse press to select justification."""
        for justify_type, pos in self.buttons.items():
            rect = QRect(pos[0], pos[1], self.button_size, self.button_size)
            if rect.contains(event.pos()):
                self.current_justify = justify_type
                self.justify_changed.emit(justify_type)
                self.update()
                break
    
    def mouseMoveEvent(self, event):
        """Handle mouse movement for hover effects."""
        old_hover = self.hover_button
        self.hover_button = None
        
        for justify_type, pos in self.buttons.items():
            rect = QRect(pos[0], pos[1], self.button_size, self.button_size)
            if rect.contains(event.pos()):
                self.hover_button = justify_type
                break
        
        if old_hover != self.hover_button:
            self.update()
    
    def leaveEvent(self, event):
        """Handle mouse leave event."""
        if self.hover_button is not None:
            self.hover_button = None
            self.update()