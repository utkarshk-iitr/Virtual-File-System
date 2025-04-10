from subprocess import run 
import json
from tabulate import tabulate
import sys
import os

def func_call(s):
    s = s.split()
    result = run(s, capture_output=True, text=True)
    return result

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

def change_dir(path):
    with open("/tmp/temp.sh", "w") as f:
        f.write(f"cd {path}\n")
        f.write("exec $SHELL\n")
    os.system("bash /tmp/temp.sh")

def delete(path):
    with open("/tmp/temp.sh", "w") as f:
        f.write(f"rm {path}\n")
        f.write("exec $SHELL\n")
    os.system("bash /tmp/temp.sh")

def move(src,dest):
    with open("/tmp/temp.sh","w") as file:
        file.write(f"mv {src} {dest}\n")
        file.write("exec $SHELL\n")
    os.system("bash /tmp/temp.sh")

def copy(src,dest):
    with open("/tmp/temp.sh","w") as file:
        file.write(f"cp {src} {dest}\n")
        file.write("exec $SHELL\n")
    os.system("bash /tmp/temp.sh")

def command(a):
    result = func_call(a)
    error = result.stderr.strip()
    result = result.stdout.strip()
    if error: print(error)
    else: print(result)

def help():
    print("\nAvailable commands:")
    print("  scan - Scan and list all devices")
    print("  mount <identifier> [mount_point] - Mount a device")
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
    print("  exit - Exit the program\n")


while True:
    input_str = input("vfs > ").strip().split()
    if input_str[0] == "exit":
        break

    elif input_str[0] == "scan":
        scan()

    elif input_str[0] == "help":
        help()

    elif input_str[0] == "cd":
        if len(input_str) > 1:
            path = input_str[1]
            change_dir(path)
        else:
            print("Usage: cd <path>")
    
    elif input_str[0] == "delete":
        if len(input_str) > 1:
            path = input_str[1]
            delete(path)
        else:
            print("Usage: delete <path>")

    elif input_str[0] == "move":
        if len(input_str) > 2:
            src = input_str[1]
            dest = input_str[2]
            move(src, dest)
        else:
            print("Usage: move <source> <destination>")

    elif input_str[0] == "copy":
        if len(input_str) > 2:
            src = input_str[1]
            dest = input_str[2]
            copy(src, dest)
        else:
            print("Usage: copy <source> <destination>")

    elif input_str[0] == "ls":
        command("ls")
    elif input_str[0] == "pwd":
        command("pwd")
    elif input_str[0] == "print":
        if len(input_str) > 1:
            file_path = input_str[1]
            command(f"cat {file_path}")
        else:
            print("Usage: print <file>")

    else:
        print("Invalid command.")