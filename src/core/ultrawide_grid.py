from typing import List, Tuple, Optional, Dict
from PyQt5.QtCore import QRect, QPoint
import math

class UltrawideGridSystem:
    """Enhanced grid system for ultrawide monitor support."""
    
    def __init__(self, monitor_rect: QRect, grid_config: dict):
        self.monitor_rect = monitor_rect
        self.columns = grid_config.get('columns', 12)
        self.rows = grid_config.get('rows', 4)
        self.subdivisions = grid_config.get('subdivisions', False)
        self.zones = grid_config.get('ultrawide_zones', [(0.0, 1.0)])
        
        # Calculate grid dimensions
        self.cell_width = monitor_rect.width() / self.columns
        self.cell_height = monitor_rect.height() / self.rows
        
        if self.subdivisions:
            self.subcell_width = self.cell_width / 2
            self.subcell_height = self.cell_height / 2
        
        self.snap_guides = []  # Store snap guidelines
        self.is_ultrawide = len(self.zones) > 1
    
    def get_cell_rect(self, col: int, row: int) -> QRect:
        """Get rectangle for a specific grid cell."""
        x = self.monitor_rect.x() + (col * self.cell_width)
        y = self.monitor_rect.y() + (row * self.cell_height)
        return QRect(int(x), int(y), 
                    int(self.cell_width), int(self.cell_height))
    
    def get_subcell_rect(self, col: int, row: int, 
                        subcol: int, subrow: int) -> QRect:
        """Get rectangle for a subdivision within a cell."""
        if not self.subdivisions:
            return self.get_cell_rect(col, row)
            
        cell_rect = self.get_cell_rect(col, row)
        x = cell_rect.x() + (subcol * self.subcell_width)
        y = cell_rect.y() + (subrow * self.subcell_height)
        return QRect(int(x), int(y), 
                    int(self.subcell_width), int(self.subcell_height))
    
    def get_zone_rect(self, zone_index: int) -> Optional[QRect]:
        """Get rectangle for a predefined zone."""
        if zone_index >= len(self.zones):
            return None
            
        start, end = self.zones[zone_index]
        x = self.monitor_rect.x() + (start * self.monitor_rect.width())
        width = (end - start) * self.monitor_rect.width()
        
        return QRect(
            int(x),
            self.monitor_rect.y(),
            int(width),
            self.monitor_rect.height()
        )
    
    def snap_to_grid(self, rect: QRect, use_subdivisions: bool = False) -> QRect:
        """Snap a rectangle to nearest grid position."""
        # Clear previous snap guides
        self.snap_guides.clear()
        
        # Determine grid size
        grid_width = self.subcell_width if use_subdivisions else self.cell_width
        grid_height = self.subcell_height if use_subdivisions else self.cell_height
        
        # Calculate nearest grid positions
        x = round((rect.x() - self.monitor_rect.x()) / grid_width) * grid_width
        y = round((rect.y() - self.monitor_rect.y()) / grid_height) * grid_height
        width = round(rect.width() / grid_width) * grid_width
        height = round(rect.height() / grid_height) * grid_height
        
        # Ensure minimum size
        width = max(width, grid_width)
        height = max(height, grid_height)
        
        # Adjust to monitor bounds
        x = max(self.monitor_rect.x(), 
                min(x, self.monitor_rect.right() - width))
        y = max(self.monitor_rect.y(), 
                min(y, self.monitor_rect.bottom() - height))
        
        # Create snap guides
        snapped_rect = QRect(int(x), int(y), int(width), int(height))
        self._create_snap_guides(snapped_rect)
        
        return snapped_rect
    
    def snap_to_zone(self, rect: QRect, point: QPoint) -> QRect:
        """Snap a rectangle to nearest zone based on point."""
        # Clear previous snap guides
        self.snap_guides.clear()
        
        relative_x = (point.x() - self.monitor_rect.x()) / self.monitor_rect.width()
        
        for i, (start, end) in enumerate(self.zones):
            if start <= relative_x <= end:
                zone_rect = self.get_zone_rect(i)
                if zone_rect:
                    snapped_rect = QRect(
                        zone_rect.x(),
                        rect.y(),
                        zone_rect.width(),
                        rect.height()
                    )
                    
                    # Create snap guides
                    self._create_snap_guides(snapped_rect)
                    return snapped_rect
        
        return rect
    
    def get_grid_lines(self) -> Dict[str, List[Tuple[QPoint, QPoint]]]:
        """Get all grid lines for rendering."""
        lines = {
            'main': [],    # Main grid lines
            'sub': [],     # Subdivision lines
            'zones': []    # Zone dividers
        }
        
        # Main grid lines
        for col in range(self.columns + 1):
            x = self.monitor_rect.x() + (col * self.cell_width)
            lines['main'].append((
                QPoint(int(x), self.monitor_rect.y()),
                QPoint(int(x), self.monitor_rect.bottom())
            ))
        
        for row in range(self.rows + 1):
            y = self.monitor_rect.y() + (row * self.cell_height)
            lines['main'].append((
                QPoint(self.monitor_rect.x(), int(y)),
                QPoint(self.monitor_rect.right(), int(y))
            ))
        
        # Subdivision lines
        if self.subdivisions:
            for col in range(self.columns):
                for row in range(self.rows):
                    cell_rect = self.get_cell_rect(col, row)
                    
                    # Vertical subdivision
                    x = cell_rect.x() + (cell_rect.width() / 2)
                    lines['sub'].append((
                        QPoint(int(x), cell_rect.y()),
                        QPoint(int(x), cell_rect.bottom())
                    ))
                    
                    # Horizontal subdivision
                    y = cell_rect.y() + (cell_rect.height() / 2)
                    lines['sub'].append((
                        QPoint(cell_rect.x(), int(y)),
                        QPoint(cell_rect.right(), int(y))
                    ))
        
        # Zone lines
        for start, _ in self.zones[1:]:  # Skip first zone start
            x = self.monitor_rect.x() + (start * self.monitor_rect.width())
            lines['zones'].append((
                QPoint(int(x), self.monitor_rect.y()),
                QPoint(int(x), self.monitor_rect.bottom())
            ))
        
        return lines
    
    def get_suggested_layouts(self) -> List[List[QRect]]:
        """Get predefined layout suggestions."""
        layouts = []
        
        # 1. Zone-based layout
        if self.is_ultrawide:
            layout = []
            for i in range(len(self.zones)):
                layout.append(self.get_zone_rect(i))
            layouts.append(layout)
        
        # 2. Main work area with side panels
        main_width = self.monitor_rect.width() * 0.5
        side_width = (self.monitor_rect.width() - main_width) / 2
        layouts.append([
            QRect(self.monitor_rect.x(), self.monitor_rect.y(), 
                  int(side_width), self.monitor_rect.height()),
            QRect(int(self.monitor_rect.x() + side_width), self.monitor_rect.y(),
                  int(main_width), self.monitor_rect.height()),
            QRect(int(self.monitor_rect.right() - side_width), self.monitor_rect.y(),
                  int(side_width), self.monitor_rect.height())
        ])
        
        # 3. Grid-based layouts
        grid_layout = []
        for col in range(self.columns):
            for row in range(self.rows):
                grid_layout.append(self.get_cell_rect(col, row))
        layouts.append(grid_layout)
        
        return layouts
    
    def _create_snap_guides(self, rect: QRect):
        """Create snap guidelines for visualization."""
        self.snap_guides = [
            # Vertical guides
            (QPoint(rect.left(), self.monitor_rect.top()),
             QPoint(rect.left(), self.monitor_rect.bottom())),
            (QPoint(rect.right(), self.monitor_rect.top()),
             QPoint(rect.right(), self.monitor_rect.bottom())),
            
            # Horizontal guides
            (QPoint(self.monitor_rect.left(), rect.top()),
             QPoint(self.monitor_rect.right(), rect.top())),
            (QPoint(self.monitor_rect.left(), rect.bottom()),
             QPoint(self.monitor_rect.right(), rect.bottom()))
        ]