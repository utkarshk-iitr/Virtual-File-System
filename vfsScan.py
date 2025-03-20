from subprocess import run 
import json
from tabulate import tabulate

def func_call(s):
    s = s.split()
    result = run(s, capture_output=True, text=True)
    return result

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