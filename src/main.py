import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup, QPoint, QTimer, pyqtSignal
# New imports for window and keyboard handling
import keyboard
import win32gui
import win32con
import win32api

from core.layer_manager import LayerManager
from core.monitor_profiles import MonitorProfileManager
from core.window_animator import WindowAnimator  # Added missing animator import
from components.floating_button import FloatingActionButton
from components.grid_overlay import GridOverlay
from components.preview_rect import PreviewRect
from components.justify_controls import JustifyControls
from core.ultrawide_grid import JustifyType
from core.ultrawide_grid import UltrawideGridSystem
from components.settings_dialog import SettingsDialog


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

        # UI Components with proper initialization
        screen = QApplication.primaryScreen().geometry()
        
        # Create basic grid system
        self.grid_overlay = GridOverlay(settings=self.settings)
        self.grid_overlay.setGeometry(screen)
        
        basic_grid = UltrawideGridSystem(
            monitor_rect=screen,
            grid_config={
                'columns': self.settings.get('grid_cols', 6),
                'rows': self.settings.get('grid_rows', 4),
                'subdivisions': False,
                'ultrawide_zones': [(0.0, 1.0)]
            }
        )
        
        # Set the grid system
        self.grid_overlay.update_grid_systems({'primary': basic_grid})
        self.grid_overlay.set_active_monitor('primary')
        
        # Initialize preview rect
        self.preview = PreviewRect()
        
        # Initialize justify controls
        self.justify_controls = JustifyControls()
        
        # Initialize window animator
        self.window_animator = WindowAnimator()

        # State tracking
        self.menu_open = False
        self.dragging_window = False
        self.current_window = None

        # New drag detection state
        self.dragging_active = False
        self.shift_pressed = False
        self.drag_timer = QTimer()
        self.drag_timer.setInterval(16)  # ~60fps check for drag
        self.drag_timer.timeout.connect(self.check_drag_state)

        # Setup UI and connections
        self.init_ui()
        self.setup_connections()
        
        # Start monitoring for window drags
        self.setup_shortcuts()
        self.drag_timer.start()
        
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
            'settings': FloatingActionButton(size=56, text="⚙", icon_color="#2196F3"),
            'pin': FloatingActionButton(size=56, text="📌", icon_color="#FFC107")  # New pin button
        }

        # Set tooltips
        self.menu_bubbles['new_layer'].setToolTip("New Layer")
        self.menu_bubbles['cancel'].setToolTip("Cancel")
        self.menu_bubbles['confirm'].setToolTip("Confirm")
        self.menu_bubbles['settings'].setToolTip("Settings")
        self.menu_bubbles['pin'].setToolTip("Pin Window")

        # Position justify controls
        justify_x = screen.width() - self.justify_controls.width() - 20
        justify_y = (screen.height() - self.justify_controls.height()) // 2
        self.justify_controls.move(justify_x, justify_y)

        # Hide controls initially
        self.justify_controls.hide()
        for bubble in self.menu_bubbles.values():
            bubble.hide()

    def setup_connections(self):
        """Setup signal connections."""
        # Main FAB connections
        self.main_fab.clicked.connect(self.toggle_menu)
        self.main_fab.moved.connect(self.update_bubble_positions)

        # Menu bubble connections
        self.menu_bubbles['new_layer'].clicked.connect(self.create_new_layer)
        self.menu_bubbles['cancel'].clicked.connect(self.cancel_layout)
        self.menu_bubbles['confirm'].clicked.connect(self.save_layout)
        self.menu_bubbles['settings'].clicked.connect(self.open_settings)
        self.menu_bubbles['pin'].clicked.connect(self.toggle_pin_current_window)

        # Justify controls connection
        self.justify_controls.justify_changed.connect(self.apply_justification)

    def update_bubble_positions(self, main_pos=None):
        """Update positions of menu bubbles relative to main FAB."""
        if main_pos is None:
            main_pos = self.main_fab.pos()

        # Define bubble positions relative to main FAB
        bubble_positions = {
            'new_layer': QPoint(0, -100),    # North
            'cancel': QPoint(-100, 0),       # West
            'confirm': QPoint(100, 0),       # East
            'settings': QPoint(0, 100),      # South
            'pin': QPoint(-70, -70)          # Northwest
        }

        # Update positions
        for name, bubble in self.menu_bubbles.items():
            target_pos = main_pos + bubble_positions[name]
            if self.menu_open:
                bubble.move(target_pos)
            else:
                bubble.move(main_pos)

    def toggle_menu(self):
        """Toggle the grid overlay and bubble menu."""
        # Move all bubbles to main button position first
        main_pos = self.main_fab.pos()
        for bubble in self.menu_bubbles.values():
            bubble.move(main_pos)

        self.menu_open = not self.menu_open

        if self.menu_open:
            print("Opening menu...")
            # Show grid overlay
            screen = QApplication.primaryScreen().geometry()
            self.grid_overlay.setGeometry(screen)
            self.grid_overlay.show_overlay()
            
            # Show justify controls
            self.justify_controls.show_controls()
            
            # Show bubbles
            for bubble in self.menu_bubbles.values():
                bubble.show()
                bubble.raise_()
            self.update_bubble_positions()
        else:
            print("Closing menu...")
            # Hide everything
            self.grid_overlay.hide_overlay()
            self.justify_controls.hide_controls()
            self.hide_bubbles()

    def apply_justification(self, justify_type: JustifyType):
        """Apply selected justification to current layout."""
        if not self.menu_open:
            return
            
        # Get active monitor's grid system
        grid_system = self.grid_overlay.grid_systems.get(self.grid_overlay.active_monitor)
        if not grid_system:
            return
            
        # Calculate new positions
        current_windows = self.layer_manager.get_current_windows()
        new_positions = grid_system.calculate_justified_layout(current_windows, justify_type)
        
        # Apply new positions with animation
        for handle, rect in new_positions.items():
            self.window_animator.animate_window(handle, rect)

    def toggle_pin_current_window(self):
        """Toggle pin state for current window."""
        if self.current_window:
            self.grid_overlay.toggle_window_pin(self.current_window)
            grid_system = self.grid_overlay.grid_systems.get(self.grid_overlay.active_monitor)
            if grid_system:
                grid_system.toggle_window_pin(self.current_window)

    def hide_bubbles(self):
        """Hide the bubbles and reset their states."""
        main_pos = self.main_fab.pos()
        for bubble in self.menu_bubbles.values():
            bubble.is_pressed = False
            bubble.hover = False
            bubble.move(main_pos)
            bubble.hide()
            bubble.update()

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

    def save_layout(self):
        """Save the current layout."""
        if not self.menu_open:
            return
        print("Saving layout...")
        self.layer_manager.save_layers()
        self.toggle_menu()

    def cancel_layout(self):
        """Cancel current layout changes."""
        if not self.menu_open:
            return
        print("Canceling layout changes...")
        self.layer_manager.discard_changes()
        self.toggle_menu()

    def open_settings(self):
        """Open the settings modal window."""
        if not self.menu_open:
            return
        print("Opening settings...")
        self.toggle_menu()  # Close menu first
        
        # Create and show the new settings dialog
        settings_dialog = SettingsDialog(settings=self.settings, parent=self.main_fab)
        settings_dialog.settings_changed.connect(self.apply_settings)
        settings_dialog.exec_()

    def apply_settings(self, new_settings: dict):
        """Apply new settings."""
        self.settings.update(new_settings)
        # Save settings to file
        with open(os.path.join(self.config_path, 'default_settings.json'), 'w') as f:
            json.dump(self.settings, f, indent=2)
        
        # Update components with new settings
        self.grid_overlay.settings = self.settings
        self.grid_overlay.update()
        if 'animation_duration' in new_settings:
            self.window_animator.set_default_duration(new_settings['animation_duration'])

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
            'justify_color': '#2196F3',
            'pin_color': '#FFC107',
            'fab_size': 56,
            'grid_cols': 6,
            'grid_rows': 4,
            'marker_size': 8,
            'snap_enabled': True,
            'snap_threshold': 15,
            'animation_duration': 300,
            'preview_duration': 200,
            'animation_easing': 'OutCubic'
        }

        os.makedirs(self.config_path, exist_ok=True)
        with open(os.path.join(self.config_path, 'default_settings.json'), 'w') as f:
            json.dump(settings, f, indent=2)

        return settings

    # New methods for window dragging and shortcuts
    def setup_shortcuts(self):
        """Setup global keyboard shortcuts."""
        keyboard.on_press_key('shift', self.on_shift_press)
        keyboard.on_release_key('shift', self.on_shift_release)
        keyboard.add_hotkey('esc', self.cancel_layout)
        
        # Add shortcuts for layer switching
        for i in range(1, 10):
            keyboard.add_hotkey(f'ctrl+{i}', lambda x=i: self.switch_layer(x))

    def on_shift_press(self, _):
        """Handle shift key press."""
        self.shift_pressed = True
        if self.dragging_active:
            self.show_grid_overlay()

    def on_shift_release(self, _):
        """Handle shift key release."""
        self.shift_pressed = False
        if not self.menu_open:
            self.grid_overlay.hide_overlay()

    def check_drag_state(self):
        """Monitor window dragging state."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            
            # Skip if it's our own window
            if any(hwnd == bubble.winId() for bubble in self.menu_bubbles.values()):
                return
            if hwnd in [self.grid_overlay.winId(), self.justify_controls.winId()]:
                return

            mouse_pressed = win32api.GetKeyState(win32con.VK_LBUTTON) < 0
            cursor_pos = win32gui.GetCursorPos()
            window_under_cursor = win32gui.WindowFromPoint(cursor_pos)

            if mouse_pressed and not self.dragging_active:
                self.dragging_active = True
                self.current_window = hwnd
                if self.shift_pressed:
                    self.show_grid_overlay()
            
            elif not mouse_pressed and self.dragging_active:
                self.dragging_active = False
                if not self.menu_open:
                    self.grid_overlay.hide_overlay()
                self.handle_window_drop()

            if self.dragging_active and self.current_window:
                self.handle_window_drag()

        except Exception as e:
            print(f"Error in drag detection: {e}")

    def handle_window_drag(self):
        """Handle window being dragged."""
        if not self.current_window:
            return

        try:
            rect = win32gui.GetWindowRect(self.current_window)
            current_rect = QRect(*rect)
            
            grid_system = self.grid_overlay.grid_systems.get(self.grid_overlay.active_monitor)
            if not grid_system:
                return
            
            snapped_rect = grid_system.snap_to_grid(current_rect)
            
            self.preview.set_rect(snapped_rect)
            if not self.preview.isVisible():
                self.preview.show_preview()

        except Exception as e:
            print(f"Error during drag: {e}")

    def handle_window_drop(self):
        """Handle window being dropped after drag."""
        if not self.current_window:
            return

        try:
            rect = win32gui.GetWindowRect(self.current_window)
            current_rect = QRect(*rect)
            
            grid_system = self.grid_overlay.grid_systems.get(self.grid_overlay.active_monitor)
            if grid_system:
                snapped_rect = grid_system.snap_to_grid(current_rect)
                
                # Connect to animation completion signal
                self.window_animator.animation_completed.connect(self.on_window_animation_completed)
                
                # Start animation with feedback
                animation_success = self.window_animator.animate_window(
                    self.current_window,
                    snapped_rect,
                    self.settings.get('animation_duration', 300),
                    show_feedback=True
                )
                
                # If animation started successfully, pulse the window when done
                if animation_success and self.settings.get('show_snap_feedback', True):
                    self.window_animator.animation_completed.connect(
                        lambda hwnd: self.window_animator.pulse_window(hwnd) if hwnd == self.current_window else None
                    )

            self.preview.hide_preview()
            
            if self.menu_open:
                self.layer_manager.update_window(
                    self.current_window,
                    snapped_rect,
                    self.grid_overlay.active_monitor
                )

        except Exception as e:
            print(f"Error during drop: {e}")
        finally:
            self.current_window = None

    def switch_layer(self, index: int):
        """Switch to a specific layer by index."""
        monitor_id = self.layer_manager.get_active_monitor()
        if monitor_id:
            layers = self.layer_manager.get_monitor_layers(monitor_id)
            if 0 <= index - 1 < len(layers):
                self.layer_manager.apply_layer(layers[index - 1], monitor_id)

    def cleanup(self):
        """Cleanup resources before exit."""
        self.drag_timer.stop()
        keyboard.unhook_all()


class SettingsWindow(QDialog):
    """Settings window for application configuration."""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 500, 600)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        
        # Store current settings
        self.current_settings = {}
        self.modified_settings = {}
        
        # Define easing options
        self.easing_options = {
            'Linear': QEasingCurve.Linear,
            'InOutQuad': QEasingCurve.InOutQuad,
            'OutCubic': QEasingCurve.OutCubic,
            'OutQuint': QEasingCurve.OutQuint,
            'OutElastic': QEasingCurve.OutElastic
        }

        self.setStyleSheet("""
            QDialog {
                background-color: #2C2C2C;
                border-radius: 8px;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QSlider {
                height: 20px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #4A4A4A;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #5A5A5A;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QGroupBox {
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QSpinBox, QComboBox {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                min-width: 70px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background: #4A4A4A;
                width: 20px;
            }
            QComboBox::drop-down {
                border: none;
                background: #4A4A4A;
                width: 20px;
            }
            QColorDialog {
                background-color: #2C2C2C;
            }
        """)

        self.init_ui()

    def init_ui(self):
        """Initialize settings UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Grid Settings
        grid_group = QGroupBox("Grid Settings")
        grid_layout = QGridLayout()
        
        # Grid size controls
        grid_layout.addWidget(QLabel("Columns:"), 0, 0)
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(2, 24)
        self.cols_spin.valueChanged.connect(lambda v: self.update_setting('grid_cols', v))
        grid_layout.addWidget(self.cols_spin, 0, 1)

        grid_layout.addWidget(QLabel("Rows:"), 1, 0)
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(2, 24)
        self.rows_spin.valueChanged.connect(lambda v: self.update_setting('grid_rows', v))
        grid_layout.addWidget(self.rows_spin, 1, 1)
        
        # Opacity control
        grid_layout.addWidget(QLabel("Grid Opacity:"), 2, 0)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(5, 50)
        self.opacity_slider.valueChanged.connect(lambda v: self.update_setting('overlay_opacity', v))
        grid_layout.addWidget(self.opacity_slider, 2, 1)
        
        grid_group.setLayout(grid_layout)
        layout.addWidget(grid_group)

        # Color Settings
        color_group = QGroupBox("Color Settings")
        color_layout = QGridLayout()
        
        color_settings = [
            ('Grid Color', 'grid_color'),
            ('Active Cell', 'active_cell_color'),
            ('Preview', 'preview_color'),
            ('Suggestion', 'suggestion_color'),
            ('Justify', 'justify_color'),
            ('Pin', 'pin_color')
        ]
        
        for i, (label, key) in enumerate(color_settings):
            color_layout.addWidget(QLabel(f"{label}:"), i, 0)
            color_button = QPushButton()
            color_button.setFixedSize(50, 30)
            color_button.clicked.connect(lambda checked, k=key: self.pick_color(k))
            setattr(self, f"{key}_button", color_button)
            color_layout.addWidget(color_button, i, 1)

        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        # Animation Settings
        anim_group = QGroupBox("Animation Settings")
        anim_layout = QGridLayout()
        
        # Duration control
        anim_layout.addWidget(QLabel("Duration (ms):"), 0, 0)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(50, 1000)
        self.duration_spin.setSingleStep(50)
        self.duration_spin.valueChanged.connect(lambda v: self.update_setting('animation_duration', v))
        anim_layout.addWidget(self.duration_spin, 0, 1)
        
        # Easing curve selection
        anim_layout.addWidget(QLabel("Easing:"), 1, 0)
        self.easing_combo = QComboBox()
        self.easing_combo.addItems(self.easing_options.keys())
        self.easing_combo.currentTextChanged.connect(lambda t: self.update_setting('animation_easing', t))
        anim_layout.addWidget(self.easing_combo, 1, 1)

        anim_group.setLayout(anim_layout)
        layout.addWidget(anim_group)

        # Behavior Settings
        behavior_group = QGroupBox("Behavior Settings")
        behavior_layout = QGridLayout()
        
        # Snap threshold
        behavior_layout.addWidget(QLabel("Snap Threshold:"), 0, 0)
        self.snap_spin = QSpinBox()
        self.snap_spin.setRange(5, 50)
        self.snap_spin.valueChanged.connect(lambda v: self.update_setting('snap_threshold', v))
        behavior_layout.addWidget(self.snap_spin, 0, 1)

        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)

        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("background-color: #FF5252;")
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)

    def update_setting(self, key: str, value):
        """Update a setting value."""
        self.modified_settings[key] = value

    def pick_color(self, setting_key: str):
        """Open color picker for a color setting."""
        current_color = QColor(self.current_settings.get(setting_key, '#FFFFFF'))
        color_dialog = QColorDialog(current_color, self)
        color_dialog.setStyleSheet(self.styleSheet())
        
        if color_dialog.exec_():
            color = color_dialog.selectedColor()
            hex_color = color.name()
            self.modified_settings[setting_key] = hex_color
            button = getattr(self, f"{setting_key}_button")
            button.setStyleSheet(f"background-color: {hex_color};")

    def set_current_settings(self, settings: dict):
        """Set current settings and update UI."""
        self.current_settings = settings.copy()
        self.modified_settings = {}
        
        # Update UI elements
        self.cols_spin.setValue(settings.get('grid_cols', 6))
        self.rows_spin.setValue(settings.get('grid_rows', 4))
        self.opacity_slider.setValue(settings.get('overlay_opacity', 15))
        self.duration_spin.setValue(settings.get('animation_duration', 300))
        self.snap_spin.setValue(settings.get('snap_threshold', 15))
        
        # Update color buttons
        for key in ['grid_color', 'active_cell_color', 'preview_color', 
                   'suggestion_color', 'justify_color', 'pin_color']:
            color = settings.get(key, '#FFFFFF')
            button = getattr(self, f"{key}_button")
            button.setStyleSheet(f"background-color: {color};")
        
        # Set easing curve
        easing = settings.get('animation_easing', 'OutCubic')
        index = self.easing_combo.findText(easing)
        if index >= 0:
            self.easing_combo.setCurrentIndex(index)

    def save_settings(self):
        """Save modified settings and close."""
        if self.modified_settings:
            self.settings_changed.emit(self.modified_settings)
        self.accept()

def main():
    print("Starting Window Manager...")
    app = QApplication(sys.argv)
    app.setApplicationName("Window Manager")
    app.setApplicationVersion("1.0.0")

    icon_path = os.path.join('assets', 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window_manager = WindowManager()
    
    # Add cleanup connection
    app.aboutToQuit.connect(window_manager.cleanup)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()