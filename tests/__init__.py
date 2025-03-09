"""
Window Manager Test Suite

This module contains all tests for the window manager application.
Tests are organized by component and use pytest framework.
"""

import os
import sys
from pathlib import Path

# Add src directory to path for importing
src_path = Path(__file__).parent.parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Test constants
TEST_CONFIG_DIR = os.path.join(Path(__file__).parent, 'test_config')
TEST_PROFILES_DIR = os.path.join(TEST_CONFIG_DIR, 'profiles')

# Create test directories
os.makedirs(TEST_CONFIG_DIR, exist_ok=True)
os.makedirs(TEST_PROFILES_DIR, exist_ok=True)

# Mock window dimensions
MOCK_WINDOW_DIMS = {
    'standard': (800, 600),
    'ultrawide': (3440, 1440),
    'dual': [(1920, 1080), (1920, 1080)]
}

# Test window titles
TEST_WINDOWS = {
    'browser': 'Test Browser - Test Page',
    'editor': 'Test Editor - test.txt',
    'terminal': 'Test Terminal'
}

def setup_test_environment():
    """Setup test environment with mock configurations."""
    pass

def teardown_test_environment():
    """Clean up test environment after tests."""
    pass