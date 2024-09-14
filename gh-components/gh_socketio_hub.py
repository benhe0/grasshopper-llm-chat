"""
Grasshopper Python Component: Socket.IO Hub (WIP)

This will handle communication with the Flask Hub server.
"""

import json

# Placeholder - will need socketio library
# pip install python-socketio websocket-client

DEFAULT_SERVER_URL = "http://localhost:5001"

def scan_parameters():
    """TODO: Scan document for RH_IN: tagged groups"""
    # Will scan for groups named RH_IN:paramName
    pass

def send_geometry(meshes):
    """TODO: Send mesh geometry to server"""
    pass

# Main execution
print("GH Socket Hub component loaded")
print("TODO: Implement parameter scanning and geometry sending")
