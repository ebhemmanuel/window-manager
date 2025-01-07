from PyQt5.QtCore import QObject, QTimer, QRect, QTime, QEasingCurve
import win32gui
import win32con
from typing import Dict, Any

class WindowAnimator(QObject):
    """Handles smooth window movement animations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animations = {}  # Window handle -> animation data
        
        # Setup update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_animations)
        self.update_timer.setInterval(16)  # ~60 FPS
        
        # Animation settings
        self.default_duration = 300  # milliseconds
        self.easing = QEasingCurve.OutCubic
    
    def animate_window(self, hwnd: int, start_rect: QRect, end_rect: QRect, 
                      duration: int = None):
        """Start a window movement animation."""
        if not win32gui.IsWindow(hwnd):
            return
        
        if duration is None:
            duration = self.default_duration
        
        # Store animation data
        self.animations[hwnd] = {
            'start_rect': start_rect,
            'end_rect': end_rect,
            'start_time': QTime.currentTime(),
            'duration': duration
        }
        
        # Start timer if not running
        if not self.update_timer.isActive():
            self.update_timer.start()
    
    def update_animations(self):
        """Update all active window animations."""
        current_time = QTime.currentTime()
        completed = []
        
        for hwnd, data in self.animations.items():
            if not win32gui.IsWindow(hwnd):
                completed.append(hwnd)
                continue
            
            # Calculate progress
            elapsed = data['start_time'].msecsTo(current_time)
            progress = min(1.0, elapsed / data['duration'])
            
            # Apply easing
            eased_progress = self.easing.valueForProgress(progress)
            
            # Calculate current position
            current_rect = self._interpolate_rect(
                data['start_rect'],
                data['end_rect'],
                eased_progress
            )
            
            # Update window position
            try:
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOP,
                    current_rect.x(),
                    current_rect.y(),
                    current_rect.width(),
                    current_rect.height(),
                    win32con.SWP_NOACTIVATE | win32con.SWP_NOZORDER
                )
            except:
                completed.append(hwnd)
            
            # Check if animation is complete
            if progress >= 1.0:
                completed.append(hwnd)
        
        # Remove completed animations
        for hwnd in completed:
            del self.animations[hwnd]
        
        # Stop timer if no animations are active
        if not self.animations:
            self.update_timer.stop()
    
    def stop_animation(self, hwnd: int):
        """Stop animation for a specific window."""
        if hwnd in self.animations:
            del self.animations[hwnd]
            
            if not self.animations:
                self.update_timer.stop()
    
    def stop_all_animations(self):
        """Stop all active animations."""
        self.animations.clear()
        self.update_timer.stop()
    
    def is_animating(self, hwnd: int) -> bool:
        """Check if a window is currently being animated."""
        return hwnd in self.animations
    
    def set_default_duration(self, duration: int):
        """Set the default animation duration."""
        self.default_duration = max(50, min(1000, duration))
    
    def set_easing_curve(self, easing_type: QEasingCurve.Type):
        """Set the easing curve type for animations."""
        self.easing = QEasingCurve(easing_type)
    
    @staticmethod
    def _interpolate_rect(start: QRect, end: QRect, progress: float) -> QRect:
        """Interpolate between two rectangles."""
        return QRect(
            int(start.x() + (end.x() - start.x()) * progress),
            int(start.y() + (end.y() - start.y()) * progress),
            int(start.width() + (end.width() - start.width()) * progress),
            int(start.height() + (end.height() - start.height()) * progress)
        )
    
    def get_animation_state(self, hwnd: int) -> Dict[str, Any]:
        """Get current animation state for a window."""
        if hwnd not in self.animations:
            return {}
            
        data = self.animations[hwnd]
        elapsed = data['start_time'].msecsTo(QTime.currentTime())
        progress = min(1.0, elapsed / data['duration'])
        
        return {
            'progress': progress,
            'eased_progress': self.easing.valueForProgress(progress),
            'current_rect': self._interpolate_rect(
                data['start_rect'],
                data['end_rect'],
                progress
            ),
            'remaining_time': max(0, data['duration'] - elapsed)
        }