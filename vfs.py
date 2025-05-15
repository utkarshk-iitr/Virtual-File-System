#!/usr/bin/env python3
"""
Virtual File System (VFS) CLI tool with support for block devices and iOS devices via ifuse.
Requires root privileges for mounting/unmounting.
"""
import os
import sys
import json
from subprocess import run
from tabulate  import tabulate
import textwrap

# Helper to execute commands
def func_call(cmd):
    args = cmd.split()
    return run(args, capture_output=True, text=True)

# Execute arbitrary shell command (used for simple wrappers)
def command(cmd):
    script = f"#!/bin/bash\n{cmd}\n"
    path = "/tmp/vfs_temp.sh"
    with open(path, "w") as f:
        f.write(script)
    os.chmod(path, 0o700)
    os.system(path)

# Scan: list block devices and connected iOS devices
def scan():
    try:
        ios_list = func_call("idevice_id -l").stdout.strip().splitlines()
    except Exception as e:
        ios_list = []
        print(f"Error detecting iOS devices: {e}")

    blk_out = func_call("lsblk -o NAME,PATH,LABEL,UUID,SIZE,FSTYPE -J").stdout
    data = json.loads(blk_out)

    headers = ["Type", "Identifier", "Label/UDID", "Size","FSTYPE", "Mount Point"]
    rows = []

    for dev in data.get("blockdevices", []):
        for part in dev.get("children", []):
            path = part.get("path")
            if not path:
                continue
            label = part.get("label") or ""
            uuid = part.get("uuid") or ""
            size = part.get("size") or ""
            fstype = part.get("fstype") or ""
            hint = f"/mnt{path}" if fstype else ""
            rows.append(["Block", path, label or uuid,size,fstype, hint])

    for udid in ios_list:
        rows.append(["iOS", udid, "", "-","AFC", f"/mnt/iphone_{udid[:8]}"])

    print(tabulate(rows, headers=headers, tablefmt="grid"))

# Mount regular block device
def mount_device(ident):
    blk_out = func_call("lsblk -o NAME,PATH,LABEL,UUID,FSTYPE -J").stdout
    data = json.loads(blk_out)
    devmap = {}
    for dev in data.get("blockdevices", []):
        for part in dev.get("children", []):
            path = part.get("path")
            if path:
                devmap[path] = part
                label = part.get("label") or ""
                uuid = part.get("uuid") or ""
                if label:
                    devmap[label] = part
                if uuid:
                    devmap[uuid] = part

    info = devmap.get(ident)
    if not info:
        print(f"No block device matches '{ident}'")
        return
    path = info.get("path")
    mnt = os.path.join("/mnt", os.path.basename(path))
    # Create mount point with sudo
    res = func_call(f"sudo mkdir -p {mnt}")
    if res.returncode:
        print(f"Failed to create mount point {mnt}: {res.stderr}")
        return
    # Mount
    res = func_call(f"sudo mount {path} {mnt}")
    if res.returncode == 0:
        print(f"Mounted {path} at {mnt}")
    else:
        print(f"Failed to mount {path}: {res.stderr}")

# Unmount regular block device
def unmount_device(ident):
    mnt = os.path.join("/mnt", ident.replace("/dev/", ""))
    res = func_call(f"sudo umount {mnt}")
    if res.returncode == 0:
        print(f"Unmounted {mnt}")
    else:
        print(f"Failed to unmount {mnt}: {res.stderr}")

# Mount iPhone via ifuse
def mount_iphone(udid):
    mnt = os.path.join("/mnt", f"iphone_{udid[:8]}")
    res = func_call(f"sudo mkdir -p {mnt}")
    if res.returncode:
        print(f"Failed to create mount point")
        return

    # ADD THIS: change ownership to current user
    username = os.getenv("SUDO_USER") or os.getenv("USER")
    if username:
        res = func_call(f"sudo chown {username}:{username} {mnt}")
        if res.returncode:
            print(f"Failed to change ownership of {mnt}: {res.stderr}")
            return

    val = func_call("idevicepair validate").stdout
    if "SUCCESS" not in val:
        print("Device not paired or trusted. Run 'idevicepair pair' and trust the computer.")
        return

    res = func_call(f"ifuse {mnt} --udid {udid}")
    if res.returncode == 0:
        print(f"iPhone mounted at {mnt}")
    else:
        print(f"Failed to mount iPhone: {res.stderr}")

# Unmount iPhone mountpoint
def unmount_iphone(udid):
    mnt = os.path.join("/mnt", f"iphone_{udid[:8]}")
    res = func_call(f"fusermount -u {mnt}")
    if res.returncode == 0:
        print(f"Unmounted iPhone from {mnt}")
    else:
        print(f"Failed to unmount iPhone: {res.stderr}")

def show_help():
    help_text = {
        "scan": "List block and iOS devices.",
        "mount <identifier>": "Mount a block device or iPhone.",
        "umount <identifier>": "Unmount a block device or iPhone.",
        "cd <path>": "Change the current directory.",
        "ls": "List directory contents.",
        "pwd": "Show the current directory path.",
        "delete <path>": "Delete a file or directory.",
        "move <src> <dst>": "Move or rename a file/directory.",
        "copy <src> <dst>": "Copy a file or directory.",
        "print <file>": "Display file contents.",
        "write <file>": "Edit a file using nano.",
        "help": "Show this help message.",
        "exit": "Exit the VFS CLI."
    }

    print("\n\033[1mAvailable VFS CLI Commands:\033[0m\n")
    for cmd, desc in help_text.items():
        wrapped = textwrap.fill(desc, width=70, initial_indent=' ' * 5, subsequent_indent=' ' * 10)
        print(f"  \033[94m{cmd:<20}\033[0m - {wrapped}")
    print("\nNote: Mounting/unmounting may require sudo privileges.\n")

banner = r"""
    ****************************************************
    *                                                  *
    *         __      __   _____    _____              *
    *         \ \    / /  |  ___|  / ___|              *
    *          \ \  / /   | |_    | (__                *
    *           \ \/ /    |  _|   \___  \              *
    *            \  /     | |      ___) |              *
    *             \/      |_|     |____/               *
    *                                                  *       
    *            Virtual File System CLI               *
    *                                                  *
    ****************************************************
    
    Note: Some commands (mount, umount) need sudo privileges.
    Type 'help' to see available commands.
    """

# Main REPL loop
if __name__ == '__main__':
    print(banner)
    while True:
        cwd = os.getcwd()
        inp = input(f"\033[92mvfs: \033[93m{cwd} \033[0m> ").strip().split()
        if not inp:
            continue
        cmd, *args = inp
        if cmd == 'exit':
            break
        elif cmd == 'scan':
            scan()
        elif cmd == 'help':
            show_help()
        elif cmd == 'cd' and args:
            try:
                os.chdir(args[0])
            except Exception as e:
                print(f"cd error: {e}")
        elif cmd == 'ls':
            command('ls ' + ' '.join(args))
        elif cmd == 'pwd':
            print(cwd)
        elif cmd == 'delete' and args:
            if input(f"Confirm delete {args[0]}? (y/n): ").lower() == 'y':
                command('rm -rf ' + args[0])
        elif cmd == 'move' and len(args) == 2:
            command(f"mv {args[0]} {args[1]}")
        elif cmd == 'copy' and len(args) == 2:
            command(f"cp {args[0]} {args[1]}")
        elif cmd == 'print' and args:
            command('cat ' + args[0])
        elif cmd == 'write' and args:
            command('nano ' + args[0])
        elif cmd == 'mount' and args:
            ident = args[0]
            if 'dev' not in ident:
                mount_iphone(ident)
            else:
                mount_device(ident)
        elif cmd == 'umount' and args:
            ident = args[0]
            if 'dev' not in ident:
                unmount_iphone(ident)
            else:
                unmount_device(ident)
        else:
            print("Unknown command. Type 'help' for list.")