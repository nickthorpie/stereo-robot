"""This package contains all of the utilities that relate to camera processing

The camera is responsible for taking in information about three things
- Line identification
- QR code reading
- Obect detection (Not implemented)

These features are brought together in camera_client.py
"""
from .line_follow import LineFollow
from .camera_client import CameraClient
