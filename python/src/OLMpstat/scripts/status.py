import time, argparse
from OLMpstat.potentiostat import Potentiostat
################################################################################
PORT_DEFAULT  = "/dev/ttyUSB0"
DELAY_DEFAULT = 1.0 #seconds

################################################################################
# MAIN
def main():
    #parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port",
                        help = "serial port of attached device",
                        default = PORT_DEFAULT,
                       )
    parser.add_argument("-d", "--delay",
                        help = "delay of status updates [seconds]",
                        default = DELAY_DEFAULT,
                       )
    args = parser.parse_args()
    #construct the interface class
    pstat = Potentiostat(port = args.port)
    pstat.reset()
    #enter the status update loop
    delay = args.delay
    try:
        while True:
            print "---"
            info = pstat.get_status()
            for key, val in info.items():
                print "%s: %s" % (key,val)
            time.sleep(delay)
    except KeyboardInterrupt:
        pass

################################################################################
# TEST CODE
if __name__ == "__main__":
    main()
