import subprocess
import os
import time

status = subprocess.Popen("python status-server.py", shell=True, stdout=subprocess.PIPE)

while 1:
    # check every 5 minutes whether nfd is alive
    time.sleep(300)
    try:
        output=subprocess.check_output('nfd-status | grep \"memphis.edu/internal\"', shell=True)
        print(output)
    except subprocess.CalledProcessError,e:
        output=e.output
    print("output", output)
    if "memphis.edu/internal" not in output:
        try:
            status.terminate()
            status = subprocess.Popen(["python status-server.py"], stdout=subprocess.PIPE)
        except:
            pass
    else:
        pass


