from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QRect, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath
from typing import Dict, List, Tuple, Optional, Set
from core.ultrawide_grid import JustifyType

class GridOverlay(QWidget):
    """Overlay widget for displaying grid and zones."""
    
    def __init__(self, settings=None, parent=None):
        """Initialize the grid overlay."""
        super().__init__(parent)
        self.settings = settings or {}  # Use empty dict if no settings provided
        
        # Set window properties
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Grid state
        self.active_cells = set()
        self.hover_cells = set()
        self.hover_subcell = None
        self.hover_zone = None
        self.active_monitor = None
        self.grid_systems = {}  # Monitor ID -> Grid System
        
        # Pin and justify state
        self.pinned_windows: Set[int] = set()  # Set of pinned window handles
        self.current_justify = JustifyType.START
        
        # Setup fade animation
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
    
    def set_justification(self, justify_type: JustifyType):
        """Set current justification type."""
        self.current_justify = justify_type
        self.update()
    
    def toggle_window_pin(self, window_handle: int):
        """Toggle pin state for a window."""
        if window_handle in self.pinned_windows:
            self.pinned_windows.remove(window_handle)
        else:
            self.pinned_windows.add(window_handle)
        self.update()
    
    def show_overlay(self):
        """Show overlay with fade animation."""
        self.fade_animation.stop()
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.show()
        self.raise_()
        self.fade_animation.start()
    
    def hide_overlay(self):
        """Hide overlay with fade animation."""
        self.fade_animation.stop()
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()
    
    def mouseMoveEvent(self, event):
        """Handle mouse movement to highlight cells."""
        if not self.isVisible():
            return
            
        # Find active grid system
        grid_system = self.grid_systems.get(self.active_monitor)
        if not grid_system:
            return
        
        # Convert mouse position to grid cell
        mouse_pos = event.pos()
        cell_width = grid_system.cell_width
        cell_height = grid_system.cell_height
        
        # Calculate cell coordinates
        col = int((mouse_pos.x() - grid_system.monitor_rect.x()) / cell_width)
        row = int((mouse_pos.y() - grid_system.monitor_rect.y()) / cell_height)
        
        # Ensure within grid bounds
        if 0 <= col < grid_system.columns and 0 <= row < grid_system.rows:
            # Update hover cell
            old_hover_cells = self.hover_cells
            self.hover_cells = {(col, row)}
            
            # If using subdivisions, also highlight subcell
            if grid_system.subdivisions:
                subcol = int((mouse_pos.x() - grid_system.monitor_rect.x() - col * cell_width) / 
                            (cell_width / 2))
                subrow = int((mouse_pos.y() - grid_system.monitor_rect.y() - row * cell_height) / 
                            (cell_height / 2))
                self.hover_subcell = (subcol, subrow)
            
            # Check if hover changed
            if old_hover_cells != self.hover_cells:
                self.update()
                
                # Show tooltip with cell coordinates
                self.setToolTip(f"Cell: {col+1}x{row+1}")
        else:
            # Clear hover if outside grid
            if self.hover_cells:
                self.hover_cells = set()
                self.hover_subcell = None
                self.update()
                self.setToolTip("")
    
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
            
            # Draw cell markers and pinned indicators
            self._draw_cell_markers(painter, grid_system, is_active)
            
            # Draw hover feedback if active
            if is_active:
                self._draw_hover_feedback(painter, grid_system)
            
            # Draw snap guidelines if needed
            if is_active and grid_system.snap_guides:
                self._draw_snap_guidelines(painter, grid_system)
            
            # Draw justification indicators
            if is_active:
                self._draw_justify_indicators(painter, grid_system)
            
            # Draw pin indicators
            self._draw_pin_indicators(painter, grid_system)
    
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
    
    def _draw_hover_feedback(self, painter, grid_system):
        """Draw hover feedback for grid cells."""
        if not self.hover_cells:
            return
            
        # Use a semi-transparent highlight color
        hover_color = QColor(self.settings.get('hover_color', '#4CAF50'))
        hover_color.setAlpha(40)  # 15% opacity
        
        # Draw cell highlight
        for col, row in self.hover_cells:
            cell_rect = grid_system.get_cell_rect(col, row)
            painter.fillRect(cell_rect, hover_color)
            
            # Draw outline with slightly higher opacity
            outline_color = QColor(hover_color)
            outline_color.setAlpha(100)  # 40% opacity
            painter.setPen(QPen(outline_color, 2))
            painter.drawRect(cell_rect)
            
            # If subdivision is active, highlight subcell
            if grid_system.subdivisions and self.hover_subcell:
                subcol, subrow = self.hover_subcell
                subcell_rect = grid_system.get_subcell_rect(col, row, subcol, subrow)
                
                # Draw subcell with higher opacity
                subcell_color = QColor(hover_color)
                subcell_color.setAlpha(100)  # 40% opacity
                painter.fillRect(subcell_rect, subcell_color)
                
                # Draw subcell outline
                painter.setPen(QPen(outline_color, 2))
                painter.drawRect(subcell_rect)
    
    def _draw_snap_guidelines(self, painter: QPainter, grid_system):
        """Draw guidelines for snap assistance."""
        if not grid_system.snap_guides:
            return
            
        guide_color = QColor(self.settings.get('guide_color', '#00FF00'))
        guide_color.setAlpha(100)
        painter.setPen(QPen(guide_color, 1, Qt.DashLine))
        
        for guide in grid_system.snap_guides:
            painter.drawLine(guide[0], guide[1])
    
    def _draw_justify_indicators(self, painter: QPainter, grid_system):
        """Draw indicators showing current justification type."""
        indicator_color = QColor(self.settings.get('justify_color', '#4CAF50'))
        indicator_color.setAlpha(150)
        painter.setPen(QPen(indicator_color, 2))
        
        rect = grid_system.monitor_rect
        arrow_size = 20
        
        if self.current_justify == JustifyType.START:
            self._draw_justify_arrow(painter, rect.topLeft(), arrow_size, 0)
        elif self.current_justify == JustifyType.END:
            self._draw_justify_arrow(painter, rect.topRight(), arrow_size, 180)
        elif self.current_justify == JustifyType.CENTER:
            self._draw_center_indicator(painter, rect, arrow_size)
        elif self.current_justify == JustifyType.SPACE_BETWEEN:
            self._draw_space_between_indicator(painter, rect, arrow_size)
        elif self.current_justify == JustifyType.SPACE_AROUND:
            self._draw_space_around_indicator(painter, rect, arrow_size)
        elif self.current_justify == JustifyType.SPACE_EVENLY:
            self._draw_space_evenly_indicator(painter, rect, arrow_size)
    
    def _draw_pin_indicators(self, painter: QPainter, grid_system):
        """Draw indicators for pinned windows."""
        if not self.pinned_windows:
            return
            
        pin_color = QColor(self.settings.get('pin_color', '#FF5252'))
        pin_color.setAlpha(150)
        painter.setPen(QPen(pin_color, 2))
        
        pin_size = 12
        for window_handle in self.pinned_windows:
            if window_handle in grid_system.pinned_windows:
                rect = grid_system.pinned_windows[window_handle]
                self._draw_pin_icon(painter, rect.topRight(), pin_size)
    
    def _draw_justify_arrow(self, painter: QPainter, point: QPoint, size: int, angle: int):
        """Draw an arrow indicating justification direction."""
        path = QPainterPath()
        path.moveTo(point)
        path.lineTo(point + QPoint(size, size//2))
        path.lineTo(point + QPoint(size, -size//2))
        path.lineTo(point)
        painter.fillPath(path, painter.pen().color())
    
    def _draw_center_indicator(self, painter: QPainter, rect: QRect, size: int):
        """Draw center justification indicator."""
        center = rect.center()
        painter.drawLine(center - QPoint(size, 0), center + QPoint(size, 0))
        self._draw_justify_arrow(painter, center - QPoint(size, 0), size//2, 0)
        self._draw_justify_arrow(painter, center + QPoint(size, 0), size//2, 180)
    
    def _draw_space_between_indicator(self, painter: QPainter, rect: QRect, size: int):
        """Draw space-between justification indicator."""
        y = rect.top() + size
        x_start = rect.left() + size * 2
        x_end = rect.right() - size * 2
        
        # Draw arrows pointing outward
        painter.drawLine(x_start, y, x_end, y)
        self._draw_justify_arrow(painter, QPoint(x_start, y), size//2, 180)
        self._draw_justify_arrow(painter, QPoint(x_end, y), size//2, 0)
    
    def _draw_space_around_indicator(self, painter: QPainter, rect: QRect, size: int):
        """Draw space-around justification indicator."""
        y = rect.top() + size
        x_start = rect.left() + size * 3
        x_end = rect.right() - size * 3
        
        # Draw arrows pointing outward with spaces
        painter.drawLine(x_start, y, x_start + size, y)
        painter.drawLine(x_end - size, y, x_end, y)
        self._draw_justify_arrow(painter, QPoint(x_start, y), size//2, 180)
        self._draw_justify_arrow(painter, QPoint(x_end, y), size//2, 0)
    
    def _draw_space_evenly_indicator(self, painter: QPainter, rect: QRect, size: int):
        """Draw space-evenly justification indicator."""
        y = rect.top() + size
        x_start = rect.left() + size * 2
        x_middle = rect.center().x()
        x_end = rect.right() - size * 2
        
        # Draw evenly spaced indicators
        painter.drawLine(x_start, y, x_end, y)
        for x in [x_start, x_middle, x_end]:
            painter.drawLine(x, y - size//2, x, y + size//2)
    
    def _draw_pin_icon(self, painter: QPainter, point: QPoint, size: int):
        """Draw a pin icon."""
        painter.drawEllipse(point, size//2, size//2)
        painter.drawLine(point - QPoint(size//2, size//2), 
                        point + QPoint(size//2, size//2))