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

def mount_device(identifier):
    device_map = get_device_info()
    mount_point = "/mnt/"+identifier
    func_call(f"sudo mkdir -p {mount_point}")

    for path, info in device_map.items():
        result = -1
        mount_cmd = ""
        if identifier == path:
            mount_cmd = f"sudo mount {identifier} {mount_point}"
        elif identifier == info["label"]:
            mount_cmd = f"sudo mount -L {identifier} {mount_point}"
        elif identifier == info["uuid"]:
            mount_cmd = f"sudo mount -U {identifier} {mount_point}"
        
        if mount_cmd!="":
            result = func_call(mount_cmd)
            if result.returncode == 0:
                print(f"Successfully mounted {identifier} at {mount_point}")
                print(f"To navigate to the mounted directory, run: cd {mount_point}")
                return
            else:
                print(f"Failed to mount {identifier}: {result.stderr.strip()}")
            return

    print(f"No matching device found for identifier: {identifier}")

def unmount_device(identifier):
    mount_point = f"/mnt/{identifier}"
    unmount_cmd = f"sudo umount {mount_point}"
    result = func_call(unmount_cmd)
    if result.returncode == 0:
        print(f"Successfully unmounted {mount_point}.")
    else:
        print(f"Failed to unmount {mount_point}: {result.stderr.strip()}")

def print_help():
    print("Usage:")
    print("  Mount: python test.py -m <identifier>")
    print("  Unmount: python test.py -u <identifier>")
    print("Identifier can be a label, path, or UUID")

if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
    print_help()
    sys.exit(1)

action = sys.argv[1]
if action == "-m" and len(sys.argv) == 3:
    identifier = sys.argv[2]
    mount_device(identifier)
elif action == "-u" and len(sys.argv) == 3:
    identifier = sys.argv[2]
    unmount_device(identifier)
else:
    print(sys.argv)
    print("Invalid arguments. Use -h or --help for usage instructions.")
    sys.exit(1)