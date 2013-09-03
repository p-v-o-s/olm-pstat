################################################################################
#Dependencies
#standard python
import time, argparse
#Automat framework provided
from automat.services.application import ApplicationBase
from automat.services.errors import handleCrash
#3rd party hardware vendor, install from Internet
#package local
import OLMpstat.pkg_info
################################################################################
#Module Constants
DELAY_DEFAULT = 1.0 #seconds

################################################################################
class Application(ApplicationBase):
    def __init__(self, delay, **kwargs):
        self.delay = delay
        ApplicationBase.__init__(self, **kwargs)

    def main_loop(self):
        pstat = self._load_device('pstat')
        try:
            while True:
                print "---"
                info = pstat.get_status()
                for key, val in info.items():
                    print "%s: %s" % (key,val)
                time.sleep(self.delay)
        except KeyboardInterrupt:
            pass
        
#-------------------------------------------------------------------------------
# MAIN
@handleCrash
def main():
    #parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port",
                        help = "serial port of attached device",
                        default = None,
                       )
    parser.add_argument("-d", "--delay",
                        help = "delay of status updates [seconds]",
                        type = float,
                        default = DELAY_DEFAULT,
                       )
    args = parser.parse_args()
    #construct the Application class and pass in commandline args
    app = Application(delay = args.delay)
    #load the application using configuration data
    config_filepath = OLMpstat.pkg_info.platform['config_filepath']
    app.load(config_filepath = config_filepath)
    #run the main loop
    app.main_loop()

################################################################################
# TEST CODE
if __name__ == "__main__":
    main()
