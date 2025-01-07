"""
Window Manager Application

A desktop window management tool with support for multiple monitors,
ultrawide displays, and advanced layout management.

Version: 1.0.0
Author: Your Name
License: MIT
"""

import os
import sys
from pathlib import Path

# Ensure src directory is in path
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Application metadata
__version__ = '1.0.0'
__author__ = 'Your Name'
__license__ = 'MIT'

# Configuration paths
CONFIG_DIR = os.path.join(src_dir, 'config')
ASSETS_DIR = os.path.join(src_dir, 'assets')
PROFILES_DIR = os.path.join(CONFIG_DIR, 'profiles')

# Ensure required directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(PROFILES_DIR, exist_ok=True)

# Import core components
from .core import *
from .models import *
from .components import *
from .utils import *

# Initialize logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(CONFIG_DIR, 'window_manager.log')),
        logging.StreamHandler()
    ]
)

# Global logger instance
logger = logging.getLogger('window_manager')