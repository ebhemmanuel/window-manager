from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from PyQt5.QtCore import QRect

@dataclass
class MonitorGridConfig:
    """Grid configuration for a monitor."""
    columns: int = 6
    rows: int = 4
    subdivisions: bool = False
    ultrawide_zones: Optional[List[Tuple[float, float]]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            'columns': self.columns,
            'rows': self.rows,
            'subdivisions': self.subdivisions,
            'ultrawide_zones': self.ultrawide_zones
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MonitorGridConfig':
        """Create from dictionary format."""
        return cls(
            columns=data.get('columns', 6),
            rows=data.get('rows', 4),
            subdivisions=data.get('subdivisions', False),
            ultrawide_zones=data.get('ultrawide_zones')
        )

@dataclass
class MonitorInfo:
    """Information about a monitor's configuration."""
    id: str
    name: str
    work_area: QRect
    is_primary: bool = False
    is_ultrawide: bool = False
    grid_config: MonitorGridConfig = field(default_factory=MonitorGridConfig)
    scale_factor: float = 1.0
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate the monitor's aspect ratio."""
        return self.work_area.width() / self.work_area.height()
    
    @property
    def effective_width(self) -> int:
        """Get scaled width."""
        return int(self.work_area.width() * self.scale_factor)
    
    @property
    def effective_height(self) -> int:
        """Get scaled height."""
        return int(self.work_area.height() * self.scale_factor)
    
    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            'id': self.id,
            'name': self.name,
            'work_area': {
                'x': self.work_area.x(),
                'y': self.work_area.y(),
                'width': self.work_area.width(),
                'height': self.work_area.height()
            },
            'is_primary': self.is_primary,
            'is_ultrawide': self.is_ultrawide,
            'grid_config': self.grid_config.to_dict(),
            'scale_factor': self.scale_factor
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MonitorInfo':
        """Create from dictionary format."""
        work_area = QRect(
            data['work_area']['x'],
            data['work_area']['y'],
            data['work_area']['width'],
            data['work_area']['height']
        )
        
        return cls(
            id=data['id'],
            name=data['name'],
            work_area=work_area,
            is_primary=data.get('is_primary', False),
            is_ultrawide=data.get('is_ultrawide', False),
            grid_config=MonitorGridConfig.from_dict(data.get('grid_config', {})),
            scale_factor=data.get('scale_factor', 1.0)
        )