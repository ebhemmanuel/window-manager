from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
from PyQt5.QtCore import QObject, pyqtSignal, QRect
from utils.window_utils import get_monitor_info
from models.monitor import MonitorInfo, MonitorGridConfig

@dataclass
class MonitorProfile:
    """A collection of monitor configurations."""
    name: str
    monitors: Dict[str, MonitorInfo]
    is_active: bool = False

class MonitorProfileManager(QObject):
    """Manages different monitor configurations and profiles."""
    
    # Signals
    profile_changed = pyqtSignal(str)  # profile_name
    profile_updated = pyqtSignal(str)  # profile_name
    
    def __init__(self, config_path: str):
        super().__init__()
        self.config_path = config_path
        self.profiles: Dict[str, MonitorProfile] = {}
        self.current_profile: Optional[str] = None
        self.load_profiles()
    
    def load_profiles(self):
        """Load monitor profiles from config file."""
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            
            for profile_data in data.get('profiles', []):
                monitors = {}
                for monitor_data in profile_data.get('monitors', {}).values():
                    # Create grid configuration
                    grid_config = MonitorGridConfig(
                        columns=monitor_data['grid'].get('columns', 6),
                        rows=monitor_data['grid'].get('rows', 4),
                        subdivisions=monitor_data['grid'].get('subdivisions', False),
                        ultrawide_zones=monitor_data['grid'].get('ultrawide_zones')
                    )
                    
                    # Create monitor info
                    monitors[monitor_data['id']] = MonitorInfo(
                        id=monitor_data['id'],
                        name=monitor_data['name'],
                        work_area=QRect(*monitor_data['work_area']),
                        is_primary=monitor_data['is_primary'],
                        is_ultrawide=monitor_data.get('is_ultrawide', False),
                        grid_config=grid_config
                    )
                
                self.profiles[profile_data['name']] = MonitorProfile(
                    name=profile_data['name'],
                    monitors=monitors,
                    is_active=profile_data.get('is_active', False)
                )
            
            # Set current profile
            for name, profile in self.profiles.items():
                if profile.is_active:
                    self.current_profile = name
                    break
            
            if not self.profiles:
                self.create_default_profile()
                
        except FileNotFoundError:
            self.create_default_profile()
    
    def create_default_profile(self):
        """Create a default profile based on current monitor setup."""
        monitors = {}
        monitor_info = get_monitor_info()
        
        for monitor_id, info in monitor_info.items():
            # Calculate aspect ratio
            work_area = info['work_area']
            aspect_ratio = work_area.width() / work_area.height()
            is_ultrawide = aspect_ratio > 2.0
            
            # Create grid config based on monitor type
            grid_config = MonitorGridConfig(
                columns=12 if is_ultrawide else 6,
                rows=4,
                subdivisions=is_ultrawide,
                ultrawide_zones=self._calculate_zones(aspect_ratio)
            )
            
            # Create monitor info
            monitors[monitor_id] = MonitorInfo(
                id=monitor_id,
                name=f"Display {len(monitors) + 1}",
                work_area=work_area,
                is_primary=info['is_primary'],
                is_ultrawide=is_ultrawide,
                grid_config=grid_config
            )
        
        # Create default profile
        self.profiles['Default'] = MonitorProfile(
            name='Default',
            monitors=monitors,
            is_active=True
        )
        
        self.current_profile = 'Default'
        self.save_profiles()
    
    def save_profiles(self):
        """Save profiles to config file."""
        data = {
            'profiles': []
        }
        
        for profile in self.profiles.values():
            monitors_data = {}
            for monitor in profile.monitors.values():
                monitors_data[monitor.id] = {
                    'id': monitor.id,
                    'name': monitor.name,
                    'work_area': [
                        monitor.work_area.x(),
                        monitor.work_area.y(),
                        monitor.work_area.width(),
                        monitor.work_area.height()
                    ],
                    'is_primary': monitor.is_primary,
                    'is_ultrawide': monitor.is_ultrawide,
                    'grid': {
                        'columns': monitor.grid_config.columns,
                        'rows': monitor.grid_config.rows,
                        'subdivisions': monitor.grid_config.subdivisions,
                        'ultrawide_zones': monitor.grid_config.ultrawide_zones
                    }
                }
            
            data['profiles'].append({
                'name': profile.name,
                'monitors': monitors_data,
                'is_active': profile.is_active
            })
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_profile(self, name: str) -> bool:
        """Create a new profile based on current monitor setup."""
        if name in self.profiles:
            return False
        
        monitors = {}
        monitor_info = get_monitor_info()
        
        # Copy settings from current profile if it exists
        current = self.profiles.get(self.current_profile)
        
        for monitor_id, info in monitor_info.items():
            if current and monitor_id in current.monitors:
                # Copy existing monitor config
                existing = current.monitors[monitor_id]
                monitors[monitor_id] = MonitorInfo(
                    id=monitor_id,
                    name=existing.name,
                    work_area=info['work_area'],
                    is_primary=info['is_primary'],
                    is_ultrawide=existing.is_ultrawide,
                    grid_config=existing.grid_config
                )
            else:
                # Create new monitor config
                aspect_ratio = info['work_area'].width() / info['work_area'].height()
                is_ultrawide = aspect_ratio > 2.0
                
                grid_config = MonitorGridConfig(
                    columns=12 if is_ultrawide else 6,
                    rows=4,
                    subdivisions=is_ultrawide,
                    ultrawide_zones=self._calculate_zones(aspect_ratio)
                )
                
                monitors[monitor_id] = MonitorInfo(
                    id=monitor_id,
                    name=f"Display {len(monitors) + 1}",
                    work_area=info['work_area'],
                    is_primary=info['is_primary'],
                    is_ultrawide=is_ultrawide,
                    grid_config=grid_config
                )
        
        self.profiles[name] = MonitorProfile(
            name=name,
            monitors=monitors,
            is_active=False
        )
        
        self.save_profiles()
        return True
    
    def activate_profile(self, name: str) -> bool:
        """Activate a specific profile."""
        if name not in self.profiles:
            return False
        
        # Deactivate current profile
        if self.current_profile:
            self.profiles[self.current_profile].is_active = False
        
        # Activate new profile
        self.profiles[name].is_active = True
        self.current_profile = name
        self.save_profiles()
        
        self.profile_changed.emit(name)
        return True
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile."""
        if name not in self.profiles or len(self.profiles) <= 1:
            return False
        
        # Can't delete active profile
        if self.current_profile == name:
            return False
        
        del self.profiles[name]
        self.save_profiles()
        return True
    
    def rename_profile(self, old_name: str, new_name: str) -> bool:
        """Rename a profile."""
        if old_name not in self.profiles or new_name in self.profiles:
            return False
        
        profile = self.profiles.pop(old_name)
        profile.name = new_name
        self.profiles[new_name] = profile
        
        if self.current_profile == old_name:
            self.current_profile = new_name
        
        self.save_profiles()
        return True
    
    @staticmethod
    def _calculate_zones(aspect_ratio: float) -> List[Tuple[float, float]]:
        """Calculate optimal zones based on aspect ratio."""
        if aspect_ratio >= 3.5:  # Super ultrawide
            return [
                (0.0, 0.25),   # Left quarter
                (0.25, 0.75),  # Center half
                (0.75, 1.0)    # Right quarter
            ]
        elif aspect_ratio >= 2.5:  # Standard ultrawide
            return [
                (0.0, 0.33),   # Left third
                (0.33, 0.67),  # Center third
                (0.67, 1.0)    # Right third
            ]
        return [
            (0.0, 0.5),    # Left half
            (0.5, 1.0)     # Right half
        ]