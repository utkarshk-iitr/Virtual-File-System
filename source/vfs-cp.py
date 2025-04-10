import os

cmd = input("> ").strip().split()

src = cmd[1]
dest = cmd[2]

with open("/tmp/copy.sh","w") as file:
    file.write(f"cp {src} {dest}\n")
    file.write("exec $SHELL\n")

os.system("bash /tmp/copy.sh")