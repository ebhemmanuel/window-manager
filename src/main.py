import sys
import os
import json
import keyboard
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from core.layer_manager import LayerManager
from core.monitor_profiles import MonitorProfileManager
from components.floating_button import FloatingActionButton
from components.grid_overlay import GridOverlay
from components.preview_rect import PreviewRect


class WindowManager:
    """Main application class that coordinates all components."""

    def __init__(self):
        print("Initializing WindowManager...")
        
        # Resolve paths
        self.config_path = os.path.abspath('config')
        self.assets_path = os.path.abspath('assets')

        # Load settings
        self.settings = self.load_settings()
        print("Settings loaded:", self.settings)
        
        # Initialize components
        self.profile_manager = MonitorProfileManager(
            os.path.join(self.config_path, 'profiles.json')
        )
        self.layer_manager = LayerManager(
            os.path.join(self.config_path, 'layers.json')
        )
        
        # Initialize UI components
        self.grid_overlay = GridOverlay(self.settings)
        self.preview = PreviewRect()
        self.fab = FloatingActionButton(self.settings.get('fab_size', 56))
        
        # Setup connections
        self.setup_connections()
        self.setup_shortcuts()
        
        # Show the floating action button
        self.fab.show()
        print("Initialization complete!")

    def load_settings(self) -> dict:
        """Load application settings."""
        settings_path = os.path.join(self.config_path, 'default_settings.json')
        try:
            with open(settings_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Settings file not found at {settings_path}. Creating default settings...")
            return self.create_default_settings()

    def create_default_settings(self) -> dict:
        """Create default settings."""
        settings = {
            'overlay_opacity': 15,
            'grid_color': '#FFFFFF',
            'active_cell_color': '#FFA500',
            'preview_color': '#00FF00',
            'suggestion_color': '#4CAF50',
            'fab_size': 56,
            'grid_cols': 6,
            'grid_rows': 4,
            'marker_size': 8,
            'snap_enabled': True,
            'snap_threshold': 15,
            'animation_duration': 300,
            'preview_duration': 200
        }
        
        os.makedirs(self.config_path, exist_ok=True)
        with open(os.path.join(self.config_path, 'default_settings.json'), 'w') as f:
            json.dump(settings, f, indent=2)
        
        return settings

    def setup_connections(self):
        """Setup signal connections between components."""
        self.layer_manager.layer_changed.connect(self.on_layer_changed)
        self.layer_manager.layer_updated.connect(self.on_layer_updated)
        self.layer_manager.unsaved_changes.connect(self.on_unsaved_changes)
        self.profile_manager.profile_changed.connect(self.on_profile_changed)
        self.profile_manager.profile_updated.connect(self.on_profile_updated)
        self.fab.clicked.connect(self.show_layer_menu)

    def setup_shortcuts(self):
        """Setup global keyboard shortcuts."""
        keyboard.add_hotkey('ctrl+shift+g', self.toggle_grid)
        keyboard.add_hotkey('ctrl+shift+space', self.show_layer_menu)
        for i in range(1, 10):
            keyboard.add_hotkey(f'ctrl+shift+{i}', lambda x=i: self.switch_layer_index(x))

    def toggle_grid(self):
        """Toggle grid overlay visibility."""
        if self.grid_overlay.isVisible():
            self.grid_overlay.hide_overlay()
        else:
            self.grid_overlay.show_overlay()

    def show_layer_menu(self):
        """Show the layer selection menu."""
        monitor_id = self.layer_manager.get_active_monitor()
        if not monitor_id:
            print("No active monitor found.")
            return
        
        try:
            layers = self.layer_manager.get_monitor_layers(monitor_id)
            print(f"Available layers for monitor {monitor_id}:", layers)
            # TODO: Show layer selection UI
        except ValueError as e:
            print(f"Error: {e}")


    def switch_layer_index(self, index: int):
        """Switch to layer by index (1-9)."""
        monitor_id = self.layer_manager.get_monitor_layers(monitor_id)
        if monitor_id:
            layers = self.layer_manager.get_monitor_layers(monitor_id)
            if 0 <= index - 1 < len(layers):
                self.layer_manager.apply_layer(layers[index - 1], monitor_id)

    def on_layer_changed(self, monitor_id: str, layer_name: str):
        """Handle layer change."""
        self.grid_overlay.update_grid_config(
            self.layer_manager.get_layer_grid_config(monitor_id)
        )

    def on_layer_updated(self, layer_name: str):
        """Handle layer update."""
        self.grid_overlay.update()

    def on_profile_changed(self, profile_name: str):
        """Handle profile change."""
        self.grid_overlay.update_monitors(
            self.profile_manager.get_profile_monitors(profile_name)
        )

    def on_profile_updated(self, profile_name: str):
        """Handle profile update."""
        if profile_name == self.profile_manager.current_profile:
            self.on_profile_changed(profile_name)

    def on_unsaved_changes(self, has_changes: bool):
        """Handle unsaved changes state."""
        print(f"Unsaved changes: {has_changes}")


def main():
    print("Starting Window Manager...")
    app = QApplication(sys.argv)
    app.setApplicationName("Window Manager")
    app.setApplicationVersion("1.0.0")

    icon_path = os.path.join('assets', 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window_manager = WindowManager()
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
