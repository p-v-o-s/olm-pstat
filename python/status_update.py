import time
import numpy as np
import pylab
from potentiostat import Potentiostat

PORT  = "/dev/ttyUSB0"
DELAY = 1.0 #seconds

if __name__ == "__main__":
    pstat = Potentiostat(port = PORT)
    pstat.reset()
    try:
        while True:
            print "---"
            info = pstat.get_status()
            for key, val in info.items():
                print "%s: %s" % (key,val)
            time.sleep(DELAY)
    except KeyboardInterrupt:
        pass
