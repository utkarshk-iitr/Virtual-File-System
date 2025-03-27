#!/usr/bin/env python3
from subprocess import run
import json
import sys

def func_call(s):
    s = s.split()
    result = run(s, capture_output=True, text=True)
    return result

def get_device_info():
    result = func_call("lsblk -o NAME,PATH,LABEL,UUID,SIZE,FSTYPE -J").stdout.strip()
    data = json.loads(result)
    device_map = {}

    for device in data.get("blockdevices", []):
        for partition in device.get("children", []):
            path = partition.get("path")
            if path:
                device_map[path] = {
                    "label": partition.get("label", "N/A"),
                    "uuid": partition.get("uuid", "N/A"),
                    "fstype": partition.get("fstype", "N/A"),
                    "name": partition.get("name", "N/A")
                }
    return device_map

def mount_device(identifier, mount_point=None):
    device_map = get_device_info()

    for path, info in device_map.items():
        if identifier in (path, info["label"], info["uuid"], info["name"]):

            fstype = info["fstype"]
            label = info["label"]
            if not mount_point and label != "N/A":
                mount_point = f"/mnt/{label}"
            elif not mount_point:
                print_help()
            # Ensure the mount point exists
            func_call(f"sudo mkdir -p {mount_point}")
            # Attempt to mount the device
            if fstype == "N/A":
                print(f"Cannot mount {identifier}: Filesystem type not detected.")
                return
            mount_cmd = f"sudo mount -t {fstype} {path} {mount_point}"
            result = func_call(mount_cmd)
            if result.returncode == 0:
                print(f"Successfully mounted {identifier} at {mount_point}")
                print(f"To navigate to the mounted directory, run: cd {mount_point}")
            else:
                print(f"Failed to mount {identifier}: {result.stderr.strip()}")
            return
    print(f"No matching device found for identifier: {identifier}")

def unmount_device(mount_point):
    unmount_cmd = f"sudo umount {mount_point}"
    result = func_call(unmount_cmd)
    if result.returncode == 0:
        print(f"Successfully unmounted {mount_point}.")
    else:
        print(f"Failed to unmount {mount_point}: {result.stderr.strip()}")

def print_help():
    print("Usage:")
    print("  Mount: python test.py -m <identifier> <mount_point>")
    print("  Unmount: python test.py -u <mount_point>")
    print("Identifier can be a device name, label, path, or UUID.")

# Main
if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
    print_help()
    sys.exit(1)

action = sys.argv[1]
if action == "-m" and len(sys.argv) == 4:
    identifier = sys.argv[2]
    mount_point = sys.argv[3]
    mount_device(identifier, mount_point)
elif action == "-m" and len(sys.argv) == 3:
    identifier = sys.argv[2]
    mount_device(identifier)
elif action == "-u" and len(sys.argv) == 3:
    mount_point = sys.argv[2]
    unmount_device(mount_point)
else:
    print(sys.argv)
    print("Invalid arguments. Use -h or --help for usage instructions.")
    sys.exit(1)