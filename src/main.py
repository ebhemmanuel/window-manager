import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup, QPoint
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

        # UI Components
        self.grid_overlay = GridOverlay(self.settings)
        self.preview = PreviewRect()

        # Setup UI and connections
        self.init_ui()
        self.setup_connections()

        # Show the main FAB
        self.main_fab.show()
        print("Initialization complete!")

    def init_ui(self):
        """Initialize the bubble menu UI."""
        print("Setting up UI...")

        # Create main FAB
        self.main_fab = FloatingActionButton(size=56, text="Main")
        self.main_fab.setToolTip("Main Menu")
        
        # Get screen geometry to center the button
        screen = QApplication.primaryScreen().geometry()
        initial_x = (screen.width() - self.main_fab.width()) // 2
        initial_y = (screen.height() - self.main_fab.height()) // 2
        self.main_fab.move(initial_x, initial_y)

        # Create menu bubbles
        self.menu_bubbles = {
            'new_layer': FloatingActionButton(size=56, text="+", icon_color="#4CAF50"),
            'cancel': FloatingActionButton(size=56, text="X", icon_color="#FF5252"),
            'confirm': FloatingActionButton(size=56, text="✔", icon_color="#4CAF50"),
            'settings': FloatingActionButton(size=56, text="⚙", icon_color="#2196F3")
        }

        # Set tooltips
        self.menu_bubbles['new_layer'].setToolTip("New Layer")
        self.menu_bubbles['cancel'].setToolTip("Cancel")
        self.menu_bubbles['confirm'].setToolTip("Confirm")
        self.menu_bubbles['settings'].setToolTip("Settings")

        # Move all bubbles to main FAB position initially and hide them
        main_pos = self.main_fab.pos()
        for bubble in self.menu_bubbles.values():
            bubble.move(main_pos)
            bubble.hide()

        # Menu state
        self.menu_open = False

    def setup_connections(self):
        """Setup signal connections."""
        # Main FAB connections
        self.main_fab.clicked.connect(self.toggle_menu)
        self.main_fab.moved.connect(self.update_bubble_positions)

        # Menu bubble connections
        self.menu_bubbles['new_layer'].clicked.connect(self.create_new_layer)
        self.menu_bubbles['cancel'].clicked.connect(self.toggle_menu)
        self.menu_bubbles['confirm'].clicked.connect(self.save_grid)
        self.menu_bubbles['settings'].clicked.connect(self.open_settings)

    def toggle_menu(self):
        """Toggle the grid overlay and bubble menu."""
        # Move all bubbles to main button position first
        main_pos = self.main_fab.pos()
        for bubble in self.menu_bubbles.values():
            bubble.move(main_pos)

        self.menu_open = not self.menu_open

        if self.menu_open:
            print("Opening menu...")
            self.grid_overlay.show_overlay()
            for bubble in self.menu_bubbles.values():
                bubble.show()
            self.update_bubble_positions()
        else:
            print("Closing menu...")
            self.grid_overlay.hide_overlay()
            self.hide_bubbles()

    def hide_bubbles(self):
        """Hide the bubbles and reset their states."""
        main_pos = self.main_fab.pos()
        for bubble in self.menu_bubbles.values():
            bubble.is_pressed = False
            bubble.hover = False
            bubble.move(main_pos)
            bubble.hide()
            bubble.update()

    def update_bubble_positions(self, main_pos=None):
        """Update positions of menu bubbles relative to main FAB."""
        if main_pos is None:
            main_pos = self.main_fab.pos()

        bubble_positions = {
            'new_layer': QPoint(0, -100),    # North
            'cancel': QPoint(-100, 0),       # West
            'confirm': QPoint(100, 0),       # East
            'settings': QPoint(0, 100)       # South
        }

        for name, bubble in self.menu_bubbles.items():
            target_pos = main_pos + bubble_positions[name]
            if self.menu_open:
                bubble.move(target_pos)
            else:
                bubble.move(main_pos)

    def create_new_layer(self):
        """Create a new layer."""
        if not self.menu_open:
            return
        print("Creating a new layer...")
        monitor_id = self.layer_manager.get_active_monitor()
        if monitor_id:
            new_layer_name = self.layer_manager.create_layer(monitor_id, 
                f"Layer {len(self.layer_manager.get_monitor_layers(monitor_id)) + 1}")
            print(f"New layer created: {new_layer_name}")
        self.toggle_menu()

    def save_grid(self):
        """Save the grid configuration."""
        if not self.menu_open:
            return
        print("Saving grid...")
        self.layer_manager.save_layers()
        self.toggle_menu()

    def open_settings(self):
        """Open the settings modal window."""
        if not self.menu_open:
            return
        print("Opening settings...")
        self.toggle_menu()  # Close menu first
        settings_window = SettingsWindow(parent=self.main_fab)
        settings_window.exec_()

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


class SettingsWindow(QDialog):
    """Settings window for application configuration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 400, 300)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_DeleteOnClose, True)  # Ensure cleanup on close
        self.setStyleSheet("border-radius: 15px; background-color: #f0f0f0;")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Settings go here"))

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def closeEvent(self, event):
        """Handle window close event."""
        event.accept()  # Ensure proper cleanup


def main():
    print("Starting Window Manager...")
    app = QApplication(sys.argv)
    app.setApplicationName("Window Manager")
    app.setApplicationVersion("1.0.0")

    icon_path = os.path.join('assets', 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window_manager = WindowManager()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()