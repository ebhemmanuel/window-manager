from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QRect, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath
from typing import Dict, List, Tuple, Optional

class GridOverlay(QWidget):
    """Overlay widget for displaying grid and zones."""
    
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Grid state
        self.active_cells = set()
        self.hover_zone = None
        self.active_monitor = None
        self.grid_systems = {}  # Monitor ID -> Grid System
        
        # Animation
        self.fade_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.fade_effect)
        
        self.fade_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def update_grid_systems(self, grid_systems: dict):
        """Update grid systems for all monitors."""
        self.grid_systems = grid_systems
        self.update()
    
    def set_active_monitor(self, monitor_id: Optional[str]):
        """Set the currently active monitor."""
        if self.active_monitor != monitor_id:
            self.active_monitor = monitor_id
            self.hover_zone = None
            self.update()
    
    def set_hover_zone(self, zone_index: Optional[int]):
        """Set the currently hovered zone."""
        if self.hover_zone != zone_index:
            self.hover_zone = zone_index
            self.update()
    
    def set_active_cells(self, cells: set):
        """Update which grid cells are active."""
        self.active_cells = cells
        self.update()
    
    def show_overlay(self):
        """Show overlay with fade animation."""
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.show()
        self.fade_animation.start()
    
    def hide_overlay(self):
        """Hide overlay with fade animation."""
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()
    
    def paintEvent(self, event):
        """Draw the grid overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw for each monitor's grid system
        for monitor_id, grid_system in self.grid_systems.items():
            is_active = monitor_id == self.active_monitor
            is_ultrawide = grid_system.is_ultrawide
            
            # Draw background overlay
            overlay_opacity = self.settings.get('overlay_opacity', 15)
            painter.fillRect(
                grid_system.monitor_rect,
                QColor(0, 0, 0, int(255 * overlay_opacity / 100))
            )
            
            # Get all grid lines
            lines = grid_system.get_grid_lines()
            
            # Draw main grid lines
            grid_color = QColor(self.settings.get('grid_color', '#FFFFFF'))
            grid_color.setAlpha(25)  # 10% opacity
            painter.setPen(QPen(grid_color, 1))
            
            for start, end in lines['main']:
                painter.drawLine(start, end)
            
            # Draw subdivision lines if enabled
            if grid_system.subdivisions:
                sub_color = QColor(grid_color)
                sub_color.setAlpha(15)  # More subtle
                painter.setPen(QPen(sub_color, 1, Qt.DashLine))
                
                for start, end in lines['sub']:
                    painter.drawLine(start, end)
            
            # Draw zone separators for ultrawide
            if is_ultrawide:
                zone_color = QColor(self.settings.get('zone_color', '#FFA500'))
                zone_color.setAlpha(40)
                painter.setPen(QPen(zone_color, 2))
                
                for start, end in lines['zones']:
                    painter.drawLine(start, end)
                
                # Draw zone highlight if hovering
                if is_active and self.hover_zone is not None:
                    zone_rect = grid_system.get_zone_rect(self.hover_zone)
                    if zone_rect:
                        highlight = QColor(zone_color)
                        highlight.setAlpha(20)
                        painter.fillRect(zone_rect, highlight)
            
            # Draw cell markers
            self._draw_cell_markers(painter, grid_system, is_active)
            
            # Draw snap guidelines if needed
            if is_active and grid_system.snap_guides:
                self._draw_snap_guidelines(painter, grid_system)
    
    def _draw_cell_markers(self, painter: QPainter, grid_system, is_active: bool):
        """Draw grid cell markers."""
        marker_size = self.settings.get('marker_size', 8)
        active_color = QColor(self.settings.get('active_cell_color', '#FFA500'))
        active_color.setAlpha(128)  # 50% opacity
        
        for col in range(grid_system.columns + 1):
            for row in range(grid_system.rows + 1):
                x = grid_system.monitor_rect.x() + (col * grid_system.cell_width)
                y = grid_system.monitor_rect.y() + (row * grid_system.cell_height)
                
                if (col, row) in self.active_cells and is_active:
                    painter.setPen(QPen(active_color, 2))
                else:
                    marker_color = QColor(self.settings.get('grid_color', '#FFFFFF'))
                    marker_color.setAlpha(76)  # 30% opacity
                    painter.setPen(QPen(marker_color, 2))
                
                # Draw "+" marker
                painter.drawLine(
                    int(x - marker_size/2), int(y),
                    int(x + marker_size/2), int(y)
                )
                painter.drawLine(
                    int(x), int(y - marker_size/2),
                    int(x), int(y + marker_size/2)
                )
    
    def _draw_snap_guidelines(self, painter: QPainter, grid_system):
        """Draw guidelines for snap assistance."""
        if not grid_system.snap_guides:
            return
            
        guide_color = QColor(self.settings.get('guide_color', '#00FF00'))
        guide_color.setAlpha(100)
        painter.setPen(QPen(guide_color, 1, Qt.DashLine))
        
        for guide in grid_system.snap_guides:
            painter.drawLine(guide[0], guide[1])