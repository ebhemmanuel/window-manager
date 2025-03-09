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
        # Load settings
        self.settings = self.load_settings()
        
        # Initialize components
        self.profile_manager = MonitorProfileManager(
            os.path.join('config', 'profiles.json')
        )
        
        self.layer_manager = LayerManager(
            os.path.join('config', 'layers.json')
        )
        
        # Initialize UI components
        self.grid_overlay = GridOverlay(self.settings)
        self.preview = PreviewRect()
        self.fab = FloatingActionButton(self.settings.get('fab_size', 56))
        
        # Setup connections
        self.setup_connections()
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
        
        # Apply grid dimensions if changed
        if 'grid_cols' in new_settings or 'grid_rows' in new_settings:
            cols = self.settings.get('grid_cols', 6)
            rows = self.settings.get('grid_rows', 4)
            for monitor_id, grid_system in self.grid_overlay.grid_systems.items():
                grid_system.columns = cols
                grid_system.rows = rows
                grid_system.cell_width = grid_system.monitor_rect.width() / cols
                grid_system.cell_height = grid_system.monitor_rect.height() / rows
                
                # Update subdivisions if enabled
                if grid_system.subdivisions:
                    grid_system.subcell_width = grid_system.cell_width / 2
                    grid_system.subcell_height = grid_system.cell_height / 2
        
        # Apply subdivision setting if changed
        if 'subdivisions' in new_settings:
            subdivisions = new_settings['subdivisions']
            for monitor_id, grid_system in self.grid_overlay.grid_systems.items():
                grid_system.subdivisions = subdivisions
                if subdivisions:
                    grid_system.subcell_width = grid_system.cell_width / 2
                    grid_system.subcell_height = grid_system.cell_height / 2
        
        # Apply animation duration if changed
        if 'animation_duration' in new_settings:
            self.window_animator.set_default_duration(new_settings['animation_duration'])
        
        # Apply animation easing if changed
        if 'animation_easing' in new_settings:
            easing_type = getattr(QEasingCurve, new_settings['animation_easing'], QEasingCurve.OutCubic)
            self.window_animator.set_easing_curve(easing_type)
        
        # Apply preview duration if changed
        if 'preview_duration' in new_settings:
            self.preview.fade_animation.setDuration(new_settings['preview_duration'])

    def load_settings(self) -> dict:
        """Load application settings."""
        try:
            settings_path = os.path.join('config', 'default_settings.json')
            with open(settings_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
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
        
        # Save default settings
        os.makedirs('config', exist_ok=True)
        with open(os.path.join('config', 'default_settings.json'), 'w') as f:
            json.dump(settings, f, indent=2)
        
        return settings
    
    def setup_connections(self):
        """Setup signal connections between components."""
        # Layer manager connections
        self.layer_manager.layer_changed.connect(self.on_layer_changed)
        self.layer_manager.layer_updated.connect(self.on_layer_updated)
        self.layer_manager.unsaved_changes.connect(self.on_unsaved_changes)
        
        # Profile manager connections
        self.profile_manager.profile_changed.connect(self.on_profile_changed)
        self.profile_manager.profile_updated.connect(self.on_profile_updated)
        
        # UI component connections
        self.fab.clicked.connect(self.show_layer_menu)
    
    def setup_shortcuts(self):
        """Setup global keyboard shortcuts."""
        # Grid control
        keyboard.add_hotkey('ctrl+shift+g', self.toggle_grid)
        keyboard.add_hotkey('ctrl+shift+space', self.show_layer_menu)
        
        # Layer switching (1-9)
        for i in range(1, 10):
            keyboard.add_hotkey(f'ctrl+shift+{i}', 
                              lambda x=i: self.switch_layer_index(x))
    
    def toggle_grid(self):
        """Toggle grid overlay visibility."""
        if self.grid_overlay.isVisible():
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

    def on_window_animation_completed(self, hwnd):
        """Handle window animation completion."""
        # Disconnect the signal to avoid memory leaks
        try:
            self.window_animator.animation_completed.disconnect(self.on_window_animation_completed)
        except TypeError:
            # Signal was not connected
            pass
        
        # Update the layer manager if needed
        if self.menu_open and hwnd == self.current_window:
            try:
                rect = win32gui.GetWindowRect(hwnd)
                current_rect = QRect(*rect)
                self.layer_manager.update_window(
                    hwnd,
                    current_rect,
                    self.grid_overlay.active_monitor
                )
            except Exception as e:
                print(f"Error updating window after animation: {e}")

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
    
    # Event handlers
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
        # TODO: Show indicator in UI

def main():
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Window Manager")
    app.setApplicationVersion("1.0.0")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Load icon if available
    icon_path = os.path.join('assets', 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and initialize window manager
    window_manager = WindowManager()
    
    # Start event loop
    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())