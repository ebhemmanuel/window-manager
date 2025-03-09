from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                            QLabel, QSpinBox, QSlider, QPushButton, QTabWidget,
                            QColorDialog, QCheckBox, QComboBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap

class ColorButton(QPushButton):
    """Custom button for color selection with preview."""
    
    def __init__(self, color="#FFFFFF", parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedSize(40, 24)
        self.setToolTip("Click to change color")
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()
    
    def update_style(self):
        """Update button style to show current color."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color.name()};
                border: 1px solid #555555;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 1px solid #FFFFFF;
            }}
        """)
    
    def set_color(self, color):
        """Set the button's color."""
        self.color = QColor(color)
        self.update_style()
    
    def get_color(self):
        """Get the current color."""
        return self.color.name()
    
    def paintEvent(self, event):
        """Draw color preview."""
        super().paintEvent(event)
        
        # Add a checkerboard pattern for transparency
        if self.color.alpha() < 255:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            checkerboard = QPixmap(16, 16)
            checkerboard.fill(Qt.white)
            painter.fillRect(0, 0, 8, 8, Qt.lightGray)
            painter.fillRect(8, 8, 8, 8, Qt.lightGray)
            
            painter.setOpacity(0.3)
            painter.drawPixmap(self.rect(), checkerboard)
            painter.setOpacity(1.0)

class SettingsDialog(QDialog):
    """Dialog for adjusting application settings."""
    
    settings_changed = pyqtSignal(dict)  # Signal emitted when settings are changed
    
    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        # Initialize settings
        self.settings = settings or {}
        self.modified_settings = {}
        
        # Setup UI
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the UI elements."""
        main_layout = QVBoxLayout(self)
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # Add tabs
        self.tabs.addTab(self.create_appearance_tab(), "Appearance")
        self.tabs.addTab(self.create_grid_tab(), "Grid")
        self.tabs.addTab(self.create_behavior_tab(), "Behavior")
        
        main_layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
    
    def create_appearance_tab(self):
        """Create the appearance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Color settings
        color_group = QGroupBox("Colors")
        color_layout = QGridLayout()
        
        # Define color settings to add
        color_settings = [
            ("Grid Color", "grid_color", "#FFFFFF"),
            ("Hover Color", "hover_color", "#4CAF50"),
            ("Active Cell Color", "active_cell_color", "#FFA500"),
            ("Preview Color", "preview_color", "#00FF00"),
            ("Suggestion Color", "suggestion_color", "#4CAF50")
        ]
        
        self.color_buttons = {}
        
        for row, (label_text, setting_key, default_color) in enumerate(color_settings):
            label = QLabel(f"{label_text}:")
            color_button = ColorButton(self.settings.get(setting_key, default_color))
            color_button.clicked.connect(lambda _, k=setting_key, b=color_button: self.pick_color(k, b))
            
            self.color_buttons[setting_key] = color_button
            color_layout.addWidget(label, row, 0)
            color_layout.addWidget(color_button, row, 1)
        
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        
        # Opacity settings
        opacity_group = QGroupBox("Opacity")
        opacity_layout = QGridLayout()
        
        opacity_label = QLabel("Grid Opacity:")
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(5, 50)
        self.opacity_slider.setValue(self.settings.get("overlay_opacity", 15))
        self.opacity_slider.setToolTip(f"Current: {self.opacity_slider.value()}%")
        self.opacity_slider.valueChanged.connect(
            lambda v: self.update_setting("overlay_opacity", v))
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_slider.setToolTip(f"Current: {v}%"))
        
        opacity_layout.addWidget(opacity_label, 0, 0)
        opacity_layout.addWidget(self.opacity_slider, 0, 1)
        
        opacity_group.setLayout(opacity_layout)
        layout.addWidget(opacity_group)
        
        # Animation settings
        animation_group = QGroupBox("Animations")
        animation_layout = QGridLayout()
        
        duration_label = QLabel("Animation Duration:")
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(50, 1000)
        self.duration_spin.setSingleStep(50)
        self.duration_spin.setSuffix(" ms")
        self.duration_spin.setValue(self.settings.get("animation_duration", 300))
        self.duration_spin.valueChanged.connect(
            lambda v: self.update_setting("animation_duration", v))
        
        animation_layout.addWidget(duration_label, 0, 0)
        animation_layout.addWidget(self.duration_spin, 0, 1)
        
        # Easing curve selection
        easing_label = QLabel("Easing Curve:")
        self.easing_combo = QComboBox()
        easing_options = ["Linear", "OutQuad", "InOutQuad", "OutCubic", "OutElastic"]
        self.easing_combo.addItems(easing_options)
        current_easing = self.settings.get("animation_easing", "OutCubic")
        index = easing_options.index(current_easing) if current_easing in easing_options else 3
        self.easing_combo.setCurrentIndex(index)
        self.easing_combo.currentTextChanged.connect(
            lambda t: self.update_setting("animation_easing", t))
        
        animation_layout.addWidget(easing_label, 1, 0)
        animation_layout.addWidget(self.easing_combo, 1, 1)
        
        animation_group.setLayout(animation_layout)
        layout.addWidget(animation_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return tab
    
    def create_grid_tab(self):
        """Create the grid settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Grid dimensions
        dimensions_group = QGroupBox("Grid Dimensions")
        dimensions_layout = QGridLayout()
        
        cols_label = QLabel("Columns:")
        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(2, 24)
        self.cols_spin.setValue(self.settings.get("grid_cols", 6))
        self.cols_spin.valueChanged.connect(
            lambda v: self.update_setting("grid_cols", v))
        
        rows_label = QLabel("Rows:")
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(2, 16)
        self.rows_spin.setValue(self.settings.get("grid_rows", 4))
        self.rows_spin.valueChanged.connect(
            lambda v: self.update_setting("grid_rows", v))
        
        dimensions_layout.addWidget(cols_label, 0, 0)
        dimensions_layout.addWidget(self.cols_spin, 0, 1)
        dimensions_layout.addWidget(rows_label, 1, 0)
        dimensions_layout.addWidget(self.rows_spin, 1, 1)
        
        dimensions_group.setLayout(dimensions_layout)
        layout.addWidget(dimensions_group)
        
        # Subdivision settings
        subdivision_group = QGroupBox("Subdivisions")
        subdivision_layout = QVBoxLayout()
        
        self.subdivision_check = QCheckBox("Enable Cell Subdivisions")
        self.subdivision_check.setChecked(self.settings.get("subdivisions", False))
        self.subdivision_check.toggled.connect(
            lambda v: self.update_setting("subdivisions", v))
        
        subdivision_info = QLabel(
            "Subdivisions split each cell into 4 smaller cells.\n"
            "This allows for more precise window placement,\n"
            "but can make the grid more complex."
        )
        subdivision_info.setWordWrap(True)
        subdivision_info.setStyleSheet("color: rgba(255,255,255,0.7); font-style: italic;")
        
        subdivision_layout.addWidget(self.subdivision_check)
        subdivision_layout.addWidget(subdivision_info)
        
        subdivision_group.setLayout(subdivision_layout)
        layout.addWidget(subdivision_group)
        
        # Ultrawide settings
        ultrawide_group = QGroupBox("Ultrawide Monitor Settings")
        ultrawide_layout = QVBoxLayout()
        
        self.ultrawide_check = QCheckBox("Enable Special Ultrawide Zones")
        self.ultrawide_check.setChecked(self.settings.get("enable_ultrawide_zones", True))
        self.ultrawide_check.toggled.connect(
            lambda v: self.update_setting("enable_ultrawide_zones", v))
        
        zone_info = QLabel(
            "Ultrawide zones provide special layouts optimized for\n"
            "ultrawide monitors (aspect ratio > 2.0)."
        )
        zone_info.setWordWrap(True)
        zone_info.setStyleSheet("color: rgba(255,255,255,0.7); font-style: italic;")
        
        ultrawide_layout.addWidget(self.ultrawide_check)
        ultrawide_layout.addWidget(zone_info)
        
        ultrawide_group.setLayout(ultrawide_layout)
        layout.addWidget(ultrawide_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return tab
    
    def create_behavior_tab(self):
        """Create the behavior settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Snapping settings
        snap_group = QGroupBox("Window Snapping")
        snap_layout = QGridLayout()
        
        self.snap_enabled = QCheckBox("Enable Snap-to-Grid")
        self.snap_enabled.setChecked(self.settings.get("snap_enabled", True))
        self.snap_enabled.toggled.connect(
            lambda v: self.update_setting("snap_enabled", v))
        
        threshold_label = QLabel("Snap Threshold:")
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(5, 50)
        self.threshold_spin.setSuffix(" px")
        self.threshold_spin.setValue(self.settings.get("snap_threshold", 15))
        self.threshold_spin.valueChanged.connect(
            lambda v: self.update_setting("snap_threshold", v))
        
        snap_layout.addWidget(self.snap_enabled, 0, 0, 1, 2)
        snap_layout.addWidget(threshold_label, 1, 0)
        snap_layout.addWidget(self.threshold_spin, 1, 1)
        
        snap_group.setLayout(snap_layout)
        layout.addWidget(snap_group)
        
        # Preview settings
        preview_group = QGroupBox("Window Preview")
        preview_layout = QGridLayout()
        
        preview_duration_label = QLabel("Preview Duration:")
        self.preview_duration_spin = QSpinBox()
        self.preview_duration_spin.setRange(50, 1000)
        self.preview_duration_spin.setSuffix(" ms")
        self.preview_duration_spin.setValue(self.settings.get("preview_duration", 200))
        self.preview_duration_spin.valueChanged.connect(
            lambda v: self.update_setting("preview_duration", v))
        
        preview_layout.addWidget(preview_duration_label, 0, 0)
        preview_layout.addWidget(self.preview_duration_spin, 0, 1)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Keyboard shortcuts
        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_layout = QGridLayout()
        
        shortcuts_info = QLabel(
            "Keyboard shortcuts can be used to control the application.\n"
            "Default shortcuts:\n"
            "• Ctrl+Shift+G: Toggle Grid\n"
            "• Ctrl+Shift+1-9: Switch Layouts\n"
            "• Esc: Cancel Current Action"
        )
        shortcuts_info.setWordWrap(True)
        
        shortcuts_layout.addWidget(shortcuts_info, 0, 0)
        
        shortcuts_group.setLayout(shortcuts_layout)
        layout.addWidget(shortcuts_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return tab
    
    def pick_color(self, setting_key, button):
        """Open color picker for a color setting."""
        current_color = QColor(button.get_color())
        color_dialog = QColorDialog(current_color, self)
        
        if color_dialog.exec_():
            color = color_dialog.selectedColor()
            hex_color = color.name()
            button.set_color(hex_color)
            self.update_setting(setting_key, hex_color)
    
    def update_setting(self, key, value):
        """Update a setting in the modified settings dictionary."""
        self.modified_settings[key] = value
    
    def load_settings(self):
        """Load current settings into the UI elements."""
        # This method would be called after initializing the UI
        # The initialization of each control should already set its value
        pass
    
    def save_settings(self):
        """Save the modified settings and close."""
        if self.modified_settings:
            self.settings_changed.emit(self.modified_settings)
        self.accept()