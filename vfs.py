#!/usr/bin/env python3

from subprocess import run 
import json
from tabulate import tabulate
import os

def func_call(s):
    s = s.split()
    result = run(s, capture_output=True, text=True)
    return result

def command(a):
    with open("/tmp/temp.sh","w") as file:
        file.write(f"{a}\n")
    os.system("bash /tmp/temp.sh")

def scan():
    result = func_call("lsblk -o NAME,PATH,LABEL,UUID,SIZE,FSTYPE -J").stdout.strip()
    data = json.loads(result)
    device_map = {}

    table_data = []
    headers = ["Path", "Label", "Size", "Filesystem Type", "UUID"]

    for device in data.get("blockdevices", []):
        for partition in device.get("children", []):
            path = partition.get("path")
            if path:
                device_map[path] = [partition.get("label", "N/A"),partition.get("size", "N/A"),partition.get("fstype", "N/A"),partition.get("uuid", "N/A")]
                x = [path] + device_map[path]
                if x[4] != None:
                    table_data.append(x)

    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def help():
    print("\nAvailable commands:")
    print("  scan - Scan and list all devices")
    print("  mount <identifier> - Mount a device")
    print("  umount <identifier> - Unmount a device")
    print("  cd <path> - Change directory to the specified path")   
    print("  delete <path> - Delete the specified file or directory")
    print("  move <source> <destination> - Move a file or directory")   
    print("  copy <source> <destination> - Copy a file or directory")
    print("  ls - List files in the current directory")
    print("  pwd - Print the current working directory")
    print("  print <file> - Print the contents of a file")
    print("  write <file> - Write to a file")
    print("  help - Show this help message")
    print("  exit - Exit the program")

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
    mount_point = mount_point.replace(" ","_")
    func_call(f"sudo mkdir -p {mount_point}")

    for path, info in device_map.items():
        result = -1
        mount_cmd = ""
        if identifier == path:
            mount_point = mount_point.replace("/dev/","")
            mount_cmd = f'sudo mount {path} {mount_point}'
        elif identifier == info["label"]:
            mount_cmd = f'sudo mount {path} {mount_point}'
        elif identifier == info["uuid"]:
            mount_cmd = f'sudo mount {path} {mount_point}'
        
        if mount_cmd!="":
            # print(mount_cmd)
            result = func_call(mount_cmd)
            if result.returncode == 0:
                print(f"Successfully mounted {identifier} at {mount_point}")
                print(f"To navigate to the mounted directory, run: cd {mount_point}")
                print(f"Unmount it using: umount {mount_point[5:]}")
                return
            else:
                print(f"Failed to mount {identifier}: {result.stderr.strip()}")
            return

    print(f"No matching device found for identifier: {identifier}")

def unmount_device(identifier):
    identifier = identifier.replace(" ","_")
    mount_point = f"/mnt/{identifier}"
    unmount_cmd = f"sudo umount {mount_point}"
    result = func_call(unmount_cmd)
    if result.returncode == 0:
        print(f"Successfully unmounted {mount_point}.")
    else:
        print(f"Failed to unmount {mount_point}: {result.stderr.strip()}")

print("Welcome to the Virtual File System (VFS)!")
print("Type 'help' for a list of commands")
print("Note: This program requires root privileges to mount and unmount devices")
print("Make sure to run it with sudo or as root")

while True:
    print()
    w = func_call("pwd").stdout.strip()
    input_str = input(f"\033[92mvfs: \033[94m{w} \033[0m> ").strip().split()

    if input_str[0] == "exit": break
    elif input_str[0] == "scan": scan()
    elif input_str[0] == "help": help()

    elif input_str[0] == "cd":
        if len(input_str) > 1:
            path = input_str[1]
            try: os.chdir(path)
            except: print(f"Failed to change directory to {path}")
        else:
            print("Usage: cd <path>")
    
    elif input_str[0] == "delete":
        if len(input_str) > 1:
            path = " ".join(input_str[1:])
            ch = input(f"Are you sure you want to delete ? (y/n): ").strip().lower()
            if ch == "y":
                command(f'rm -rf {path}')
                print(f"Deleted {path}")
            else:
                print("Deletion cancelled")
        else:
            print("Usage: delete <path>")

    elif input_str[0] == "move":
        if len(input_str) > 2:
            all = " ".join(input_str[1:])
            command(f'mv {all}')
        else:
            print("Usage: move <source> <destination>")

    elif input_str[0] == "copy":
        if len(input_str) > 2:
            all = " ".join(input_str[1:])
            command(f'cp {all}')
        else:
            print("Usage: copy <source> <destination>")

    elif input_str[0] == "ls" and len(input_str)==1: command("ls")
    elif input_str[0] == "pwd" and len(input_str)==1: command("pwd")

    elif input_str[0] == "print":
        if len(input_str) > 1:
            file_path = " ".join(input_str[1:])
            command(f'cat {file_path}')
        else:
            print("Usage: print <file>")

    elif input_str[0] == "write":
        if len(input_str) > 1:
            file = " ".join(input_str[1:])
            command(f'nano {file}')
        else:
            print("Usage: write <file>")
    
    elif input_str[0] == "mount":
        if len(input_str) > 1:
            identifier = " ".join(input_str[1:])
            mount_device(identifier)
        else:
            print("Usage: mount <identifier>")

    elif input_str[0] == "umount":
        if len(input_str) > 1:
            identifier = " ".join(input_str[1:])
            unmount_device(identifier)
        else:
            print("Usage: umount <identifier>")
        
    else:
        print("Invalid command")
