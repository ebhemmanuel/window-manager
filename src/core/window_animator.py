from PyQt5.QtCore import QObject, QTimer, QRect, QTime, QEasingCurve, pyqtSignal
import win32gui
import win32con
from typing import Dict, Any, Optional, List
from PyQt5.QtGui import QColor

class WindowAnimator(QObject):
    """Handles smooth window movement animations with enhanced feedback."""
    
    # Animation signals
    animation_completed = pyqtSignal(int)  # Emitted when animation completes, with window handle
    animation_started = pyqtSignal(int, QRect, QRect)  # Started: handle, start_rect, end_rect
    animation_step = pyqtSignal(int, float)  # Progress update: handle, progress
    
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
        
        # Store effects to prevent garbage collection
        self._pulse_effects = []
    
    def animate_window(self, hwnd: int, target_rect: QRect, duration: int = None, show_feedback: bool = True):
        """Start a window movement animation with visual feedback."""
        if not win32gui.IsWindow(hwnd):
            return False
        
        # Get current window position if not specified
        current_rect = QRect(*win32gui.GetWindowRect(hwnd))
        
        # Skip animation if window is already at target position
        if (current_rect == target_rect):
            return True
            
        if duration is None:
            duration = self.default_duration
        
        # Store animation data
        self.animations[hwnd] = {
            'start_rect': current_rect,
            'end_rect': target_rect,
            'start_time': QTime.currentTime(),
            'duration': duration,
            'show_feedback': show_feedback
        }
        
        # Emit signal that animation is starting
        self.animation_started.emit(hwnd, current_rect, target_rect)
        
        # Start timer if not running
        if not self.update_timer.isActive():
            self.update_timer.start()
            
        return True
    
    def update_animations(self):
        """Update all active window animations with improved feedback."""
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
            
            # Emit progress signal
            self.animation_step.emit(hwnd, progress)
            
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
            except Exception as e:
                print(f"Error animating window {hwnd}: {str(e)}")
                completed.append(hwnd)
            
            # Check if animation is complete
            if progress >= 1.0:
                completed.append(hwnd)
        
        # Remove completed animations and emit signals
        for hwnd in completed:
            if hwnd in self.animations:
                self.animation_completed.emit(hwnd)
                del self.animations[hwnd]
        
        # Stop timer if no animations are active
        if not self.animations:
            self.update_timer.stop()
    
    def animate_windows(self, windows: Dict[int, QRect], duration: int = None, 
                       staggered: bool = True, delay: int = 50):
        """Animate multiple windows, optionally with staggered timing."""
        if not windows:
            return
            
        if duration is None:
            duration = self.default_duration
            
        if staggered:
            # Start windows one by one with delay
            windows_list = list(windows.items())
            
            # Start the first window immediately
            hwnd, rect = windows_list[0]
            self.animate_window(hwnd, rect, duration)
            
            # Schedule the rest with increasing delays
            for i, (hwnd, rect) in enumerate(windows_list[1:], 1):
                QTimer.singleShot(delay * i, 
                                  lambda h=hwnd, r=rect: self.animate_window(h, r, duration))
        else:
            # Start all animations at once
            for hwnd, rect in windows.items():
                self.animate_window(hwnd, rect, duration)
    
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
    
    def pulse_window(self, hwnd: int, color: str = "#4CAF50", duration: int = 300, repeats: int = 1):
        """Create a pulse effect on a window to draw attention to it."""
        if not win32gui.IsWindow(hwnd):
            return
            
        try:
            # Dynamically import to avoid circular imports
            from components.preview_rect import PreviewRect
            
            # Create a preview rect for the pulse effect
            pulse = PreviewRect()
            pulse.set_color(QColor(color))
            pulse.set_opacity(0.0)  # Start fully transparent
            
            # Set initial position
            rect = QRect(*win32gui.GetWindowRect(hwnd))
            pulse.setGeometry(rect)
            
            # Store in a list to prevent garbage collection
            self._pulse_effects.append(pulse)
            
            # Create opacity animation sequence
            fade_in = QPropertyAnimation(pulse.fade_effect, b"opacity")
            fade_in.setDuration(duration // 2)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(0.6)
            fade_in.setEasingCurve(QEasingCurve.OutQuad)
            
            fade_out = QPropertyAnimation(pulse.fade_effect, b"opacity")
            fade_out.setDuration(duration // 2)
            fade_out.setStartValue(0.6)
            fade_out.setEndValue(0.0)
            fade_out.setEasingCurve(QEasingCurve.InQuad)
            
            # Chain animations
            fade_in.finished.connect(fade_out.start)
            
            # Handle cleanup after animation
            def cleanup():
                pulse.hide()
                if pulse in self._pulse_effects:
                    self._pulse_effects.remove(pulse)
            
            fade_out.finished.connect(cleanup)
            
            # Start the pulse
            pulse.show()
            fade_in.start()
            
            # Schedule additional pulses if requested
            if repeats > 1:
                QTimer.singleShot(duration, 
                                lambda: self.pulse_window(hwnd, color, duration, repeats-1))
        except Exception as e:
            print(f"Error creating pulse effect: {e}")
    
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