"""
Grasshopper Python Component: Socket.IO Hub

PURPOSE:
Single component that handles all WebSocket communication with Flask Hub.
Replaces param-scanner.py, receive-params.py, and geometry_callback.py.

REQUIRES:
    pip install python-socketio websocket-client

INPUTS:
    server_url: Flask Hub URL (default: http://localhost:5001)
    scan_params: Boolean - trigger param scan and registration
    meshes: Mesh or list of Meshes to send
    materials: Optional material names for meshes
    run: Boolean - enable component

OUTPUTS:
    connected: Boolean - WebSocket connection status
    received_params: Dict of param updates received from server
    status: Status message
    param_count: Number of registered parameters

ARCHITECTURE:
    - Background thread maintains persistent Socket.IO connection
    - Params are registered when scan_params is True and params change
    - Geometry is sent when meshes input changes
    - Incoming param updates are stored and output for downstream use
"""

import json
import hashlib
import threading
import time
import Grasshopper as gh
from Grasshopper.Kernel.Special import GH_NumberSlider, GH_Panel
from System import Decimal

# Use sticky dict to persist state between component runs
if "sticky" not in dir():
    sticky = {}

# Initialize sticky state
if "sio_client" not in sticky:
    sticky["sio_client"] = None
if "sio_connected" not in sticky:
    sticky["sio_connected"] = False
if "sio_thread" not in sticky:
    sticky["sio_thread"] = None
if "received_params" not in sticky:
    sticky["received_params"] = {}
if "last_params_hash" not in sticky:
    sticky["last_params_hash"] = None
if "last_mesh_hash" not in sticky:
    sticky["last_mesh_hash"] = None
if "pending_geometry" not in sticky:
    sticky["pending_geometry"] = None
if "status_message" not in sticky:
    sticky["status_message"] = "Idle"

DEFAULT_SERVER_URL = "http://localhost:5001"


def decimal_to_float(d):
    """Convert .NET Decimal to Python float"""
    return float(Decimal.ToDouble(d))


def compute_hash(data):
    """Compute MD5 hash of JSON data"""
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()


def scan_tagged_parameters():
    """Scan document for RH_IN: tagged groups and extract parameter info."""
    doc = ghenv.Component.OnPingDocument()
    if doc is None:
        return []

    parameters = []

    for obj in doc.Objects:
        if isinstance(obj, gh.Kernel.Special.GH_Group):
            nickname = obj.NickName

            if nickname and nickname.startswith("RH_IN:"):
                param_name = nickname[6:]
                group_objects = obj.ObjectsRecursive()

                slider_value = None
                slider_min = None
                slider_max = None
                description = None

                for group_obj in group_objects:
                    if isinstance(group_obj, GH_NumberSlider):
                        slider_value = decimal_to_float(group_obj.Slider.Value)
                        slider_min = decimal_to_float(group_obj.Slider.Minimum)
                        slider_max = decimal_to_float(group_obj.Slider.Maximum)

                    elif isinstance(group_obj, GH_Panel):
                        try:
                            if hasattr(group_obj, 'UserText') and group_obj.UserText:
                                description = group_obj.UserText.strip()
                            elif group_obj.VolatileData.DataCount > 0:
                                description = str(
                                    group_obj.VolatileData[0][0]).strip()
                        except:
                            pass

                if slider_value is not None:
                    param_info = {
                        "name": param_name,
                        "label": param_name,
                        "value": slider_value,
                        "min": slider_min,
                        "max": slider_max
                    }
                    if description:
                        param_info["description"] = description
                    parameters.append(param_info)

    return parameters


def find_and_set_slider(param_name, value):
    """Find a tagged slider and set its value"""
    doc = ghenv.Component.OnPingDocument()
    if doc is None:
        return False

    for obj in doc.Objects:
        if isinstance(obj, gh.Kernel.Special.GH_Group):
            nickname = obj.NickName
            if nickname == f"RH_IN:{param_name}":
                for group_obj in obj.ObjectsRecursive():
                    if isinstance(group_obj, GH_NumberSlider):
                        slider = group_obj.Slider
                        min_val = decimal_to_float(slider.Minimum)
                        max_val = decimal_to_float(slider.Maximum)
                        clamped = max(min_val, min(max_val, float(value)))
                        slider.Value = Decimal(clamped)
                        return True
    return False


def serialize_mesh(mesh):
    """Serialize a single Rhino mesh to web viewer format."""
    vertices = []
    for v in mesh.Vertices:
        vertices.append({"X": float(v.X), "Y": float(v.Y), "Z": float(v.Z)})

    normals = []
    for n in mesh.Normals:
        normals.append({"X": float(n.X), "Y": float(n.Y), "Z": float(n.Z)})

    faces = []
    for f in mesh.Faces:
        if f.IsTriangle:
            faces.append({"A": f.A, "B": f.B, "C": f.C, "D": f.C})
        elif f.IsQuad:
            faces.append({"A": f.A, "B": f.B, "C": f.C, "D": f.D})

    return {"meshData": {"vertices": vertices, "normals": normals, "faces": faces}}


def serialize_meshes(mesh_list, mat_list):
    """Serialize multiple meshes with materials."""
    result = []
    for i, mesh in enumerate(mesh_list):
        if mesh is None:
            continue
        material = mat_list[i] if i < len(mat_list) else "default"
        mesh_data = serialize_mesh(mesh)
        mesh_data["metaData"] = {"material": material}
        result.append({"mesh": mesh_data})
    return result


def compute_mesh_hash(mesh_list):
    """Compute hash for change detection."""
    if not mesh_list:
        return None
    parts = []
    for mesh in mesh_list:
        if mesh is None:
            continue
        vcount = mesh.Vertices.Count
        bbox = mesh.GetBoundingBox(False)
        min_pt = bbox.Min
        max_pt = bbox.Max
        parts.append(
            f"{vcount}:{min_pt.X:.4f},{min_pt.Y:.4f},{min_pt.Z:.4f}:{max_pt.X:.4f},{max_pt.Y:.4f},{max_pt.Z:.4f}")
    return hashlib.md5("|".join(sorted(parts)).encode()).hexdigest()


def init_socketio(url):
    """Initialize Socket.IO client with event handlers."""
    try:
        import socketio
    except ImportError:
        sticky["status_message"] = "Error: pip install python-socketio websocket-client"
        return None

    # Use synchronous client for GH compatibility
    sio = socketio.Client(
        reconnection=True,
        reconnection_attempts=10,
        reconnection_delay=1,
        reconnection_delay_max=5,
        logger=False,
        engineio_logger=False
    )

    @sio.event
    def connect():
        sticky["sio_connected"] = True
        sticky["status_message"] = "Connected to Flask Hub"
        sticky["needs_gh_connect"] = True  # Will emit gh_connect in main thread
        print(f"[GH-Socket] Connected to {url}")

    @sio.event
    def disconnect():
        sticky["sio_connected"] = False
        sticky["status_message"] = "Disconnected"
        print("[GH-Socket] Disconnected")

    @sio.event
    def connect_error(data):
        sticky["sio_connected"] = False
        sticky["status_message"] = f"Connection error: {data}"
        print(f"[GH-Socket] Connection error: {data}")

    @sio.on('params_to_gh')
    def on_params_to_gh(data):
        """Receive parameter updates from Flask Hub."""
        params = data.get('params', {})
        request_id = data.get('request_id', 'unknown')
        print(f"[GH-Socket] Received params_to_gh: {params}")
        sticky["received_params"] = params
        sticky["pending_request_id"] = request_id
        # Set sliders
        for name, value in params.items():
            find_and_set_slider(name, value)

    @sio.on('params_ack')
    def on_params_ack(data):
        print(f"[GH-Socket] Params acknowledged: {data.get('status')}")

    @sio.on('geometry_ack')
    def on_geometry_ack(data):
        print(f"[GH-Socket] Geometry acknowledged: {data.get('status')}")
        sticky["status_message"] = f"Geometry sent ({data.get('mesh_count', 0)} meshes)"

    return sio


def ensure_connection(url):
    """Ensure Socket.IO client is connected."""
    if sticky["sio_client"] is None or not sticky["sio_connected"]:
        # Disconnect existing client if any
        if sticky["sio_client"] is not None:
            try:
                sticky["sio_client"].disconnect()
            except:
                pass

        # Create new client
        sio = init_socketio(url)
        if sio is None:
            return False

        sticky["sio_client"] = sio

        # Connect in background thread
        def connect_thread():
            try:
                # Try polling first (more reliable), then websocket
                sio.connect(url, transports=['polling', 'websocket'], wait_timeout=10)
                # Keep thread alive for event handling
                sio.wait()
            except Exception as e:
                sticky["status_message"] = f"Connection failed: {e}"
                sticky["sio_connected"] = False
                print(f"[GH-Socket] Connection failed: {e}")
                import traceback
                traceback.print_exc()

        if sticky["sio_thread"] is None or not sticky["sio_thread"].is_alive():
            sticky["sio_thread"] = threading.Thread(
                target=connect_thread, daemon=True)
            sticky["sio_thread"].start()
            # Wait briefly for connection
            time.sleep(0.5)

    return sticky["sio_connected"]


def emit_params(params):
    """Emit params registration to Flask Hub."""
    try:
        if sticky["sio_client"] and sticky["sio_client"].connected:
            sticky["sio_client"].emit('gh_params_register', {'params': params})
            print(f"[GH-Socket] Emitted gh_params_register: {len(params)} params")
            return True
    except Exception as e:
        print(f"[GH-Socket] Error emitting params: {e}")
    return False


def emit_geometry(geometry_data, params_data=None):
    """Emit geometry to Flask Hub."""
    try:
        if sticky["sio_client"] and sticky["sio_client"].connected:
            import uuid
            request_id = sticky.get(
                "pending_request_id") or f"gh-{uuid.uuid4().hex[:8]}"
            payload = {
                'request_id': request_id,
                'geometry': geometry_data
            }
            if params_data:
                payload['params'] = params_data
            sticky["sio_client"].emit('gh_geometry', payload)
            print(f"[GH-Socket] Emitted gh_geometry: {len(geometry_data)} meshes")
            # Clear pending request_id after use
            sticky["pending_request_id"] = None
            return True
    except Exception as e:
        print(f"[GH-Socket] Error emitting geometry: {e}")
    return False


# ============================================================
# MAIN EXECUTION
# ============================================================

connected = False
received_params = {}
status = "Initializing"
param_count = 0

if run:
    url = server_url if server_url else DEFAULT_SERVER_URL

    # Ensure WebSocket connection
    connected = ensure_connection(url)

    if connected:
        status = "Connected"

        # Emit gh_connect if needed (deferred from connect event)
        if sticky.get("needs_gh_connect") and sticky["sio_client"]:
            try:
                # Check if actually connected before emitting
                if sticky["sio_client"].connected:
                    sticky["sio_client"].emit('gh_connect', {'client_type': 'grasshopper'})
                    sticky["needs_gh_connect"] = False
                    print("[GH-Socket] Emitted gh_connect")
            except Exception as e:
                print(f"[GH-Socket] Error emitting gh_connect: {e}")

        # Always scan params to detect changes (for two-way sync)
        params_list = scan_tagged_parameters()
        param_count = len(params_list)
        params_hash = compute_hash(params_list)

        # Register/update params if changed (or if scan_params forces it)
        params_changed = params_hash != sticky["last_params_hash"]
        if params_changed or scan_params:
            if emit_params(params_list):
                sticky["last_params_hash"] = params_hash
                status = f"Registered {param_count} params"
        else:
            status = f"{param_count} params (unchanged)"

        # Send geometry if meshes provided and changed
        if meshes:
            # Normalize meshes to list
            if isinstance(meshes, list):
                mesh_list = meshes
            elif hasattr(meshes, '__iter__') and not hasattr(meshes, 'Vertices'):
                mesh_list = list(meshes)
            else:
                mesh_list = [meshes]

            mesh_hash = compute_mesh_hash(mesh_list)

            if mesh_hash != sticky["last_mesh_hash"]:
                # Prepare materials
                if not materials:
                    mat_list = ["default"] * len(mesh_list)
                elif isinstance(materials, list):
                    mat_list = materials + ["default"] * \
                        (len(mesh_list) - len(materials))
                else:
                    mat_list = [materials] * len(mesh_list)

                # Always include current params with geometry for two-way sync
                current_params = params_list  # Use already-scanned params

                # Serialize and emit
                geometry_data = serialize_meshes(mesh_list, mat_list)
                if emit_geometry(geometry_data, current_params):
                    sticky["last_mesh_hash"] = mesh_hash
                    status = f"Sent {len(mesh_list)} mesh(es)"

        # Output received params
        received_params = sticky.get("received_params", {})

    else:
        status = sticky.get("status_message", "Not connected")

else:
    status = "Disabled (run=False)"
    # Disconnect if component is disabled
    if sticky["sio_client"] and sticky["sio_connected"]:
        try:
            sticky["sio_client"].disconnect()
        except:
            pass
        sticky["sio_connected"] = False
