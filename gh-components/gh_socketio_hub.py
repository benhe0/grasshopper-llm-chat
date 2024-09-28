"""
Grasshopper Python Component: Socket.IO Hub

Handles WebSocket communication with Flask Hub.
Scans parameters and sends mesh geometry.
"""

import json
import hashlib
import Grasshopper as gh
from Grasshopper.Kernel.Special import GH_NumberSlider
from System import Decimal

DEFAULT_SERVER_URL = "http://localhost:5001"


def decimal_to_float(d):
    return float(Decimal.ToDouble(d))


def scan_tagged_parameters():
    """Scan for RH_IN: tagged groups."""
    doc = ghenv.Component.OnPingDocument()
    if doc is None:
        return []

    parameters = []
    for obj in doc.Objects:
        if isinstance(obj, gh.Kernel.Special.GH_Group):
            nickname = obj.NickName
            if nickname and nickname.startswith("RH_IN:"):
                param_name = nickname[6:]
                for group_obj in obj.ObjectsRecursive():
                    if isinstance(group_obj, GH_NumberSlider):
                        parameters.append({
                            "name": param_name,
                            "value": decimal_to_float(group_obj.Slider.Value),
                            "min": decimal_to_float(group_obj.Slider.Minimum),
                            "max": decimal_to_float(group_obj.Slider.Maximum)
                        })
    return parameters


def serialize_mesh(mesh):
    """Serialize a Rhino mesh to JSON format."""
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


# Main execution
if run:
    params = scan_tagged_parameters()
    param_count = len(params)

    if meshes:
        mesh_list = meshes if isinstance(meshes, list) else [meshes]
        mat_list = materials if materials else ["default"] * len(mesh_list)
        geometry = serialize_meshes(mesh_list, mat_list)
        status = f"{param_count} params, {len(geometry)} meshes"
    else:
        status = f"{param_count} params, no meshes"
else:
    status = "Disabled"
    param_count = 0
