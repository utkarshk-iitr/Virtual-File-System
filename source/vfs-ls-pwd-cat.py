from subprocess import run 

def func_call(s):
    s = s.split()
    result = run(s, capture_output=True, text=True)
    return result

a = input("> ").strip()

li = ["ls", "pwd", "cat"]
if a.split()[0] not in li:
    print("Invalid command")
    exit()

result = func_call(a)

error = result.stderr.strip()
result = result.stdout.strip()

if error: print(error)
else: print(result)
