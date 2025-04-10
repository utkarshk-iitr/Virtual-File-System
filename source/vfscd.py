import os

new_dir = input("> ").strip().split()[1]

with open("/tmp/change_dir.sh", "w") as f:
    f.write(f"cd {new_dir}\n")
    f.write("exec $SHELL\n")  

os.system("bash /tmp/change_dir.sh")
