import os

delFile = input("> ").strip().split()[1]

with open("/tmp/remove.py","w") as file:
    file.write(f"rm {delFile}\n")
    file.write("exec $SHELL\n")

os.system("bash /tmp/remove.py")