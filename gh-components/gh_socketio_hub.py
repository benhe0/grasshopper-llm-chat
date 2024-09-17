"""
Grasshopper Python Component: Socket.IO Hub

Scans for RH_IN: tagged parameter groups and sends them to Flask Hub.
"""

import json
import Grasshopper as gh
from Grasshopper.Kernel.Special import GH_NumberSlider
from System import Decimal

DEFAULT_SERVER_URL = "http://localhost:5001"


def decimal_to_float(d):
    """Convert .NET Decimal to Python float"""
    return float(Decimal.ToDouble(d))


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

                for group_obj in group_objects:
                    if isinstance(group_obj, GH_NumberSlider):
                        slider_value = decimal_to_float(group_obj.Slider.Value)
                        slider_min = decimal_to_float(group_obj.Slider.Minimum)
                        slider_max = decimal_to_float(group_obj.Slider.Maximum)

                if slider_value is not None:
                    param_info = {
                        "name": param_name,
                        "value": slider_value,
                        "min": slider_min,
                        "max": slider_max
                    }
                    parameters.append(param_info)

    return parameters


# Main execution
if run:
    params = scan_tagged_parameters()
    param_count = len(params)
    status = f"Found {param_count} parameters"
    print(status)
    for p in params:
        print(f"  - {p['name']}: {p['value']}")
else:
    status = "Disabled"
    param_count = 0
