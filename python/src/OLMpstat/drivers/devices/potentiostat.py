###############################################################################
#Dependencies
#standard python
from StringIO import StringIO
#Automat framework provided
from automat.core.hwcontrol.devices.device import Device
from automat.core.hwcontrol.communication.serial_mixin import SerialCommunicationsMixIn
#3rd party hardware vendor, install from Internet
import numpy as np
import yaml
#package local
###############################################################################
#Module Constants
BAUDRATE = 115200
EOL  = "\n"

###############################################################################
class Interface(Device, SerialCommunicationsMixIn):
    def __init__(self, port, **kwargs):
        debug = kwargs.pop('debug', False)
        #initialize GPIB communication
        SerialCommunicationsMixIn.__init__(self,
                                           port = port,
                                           debug = debug,
                                           **kwargs)
    def initialize(self):
        self.reset()
    
    def reset(self):
        self._send("*RST")
        self._read_until_tag("</INIT>")
        
    def get_status(self):
        self._send("STATUS?")
        resp = self._read_until_tag("</STATUS>")
        info = yaml.load(resp)
        return info
        
    def set_control_voltage(self, v):
        cmd = "VCTRL %f" % v
        self._send(cmd)
        
    def measure_cell_current(self):
        resp = self._exchange("ICELL?")
        
    def do_voltage_sweep(self,
                         v_start, v_end, v_rate,
                         samp_rate = 10.0,
                         cycles = 1,
                         current_range_level = None,
                         blocking = True,
                        ):
        """ Start a voltage sweep on the controller.  Optionally according
            blocking = True, then read all the data, and parse into a numpy
            array.
        """
        v_start = float(v_start)
        v_end   = float(v_end)
        v_rate  = float(v_rate)
        cycles  = int(cycles)
        if not current_range_level is None:
            self._send("IRANGE.LEVEL %d" % current_range_level)
        self._send("VSWEEP.START %f" % v_start)
        self._send("VSWEEP.END %f" % v_end)
        self._send("VSWEEP.RAMP %f" % v_rate)
        self._send("VSWEEP.SAMPLE %f" % samp_rate)
        self._send("VSWEEP.CYCLES %d" % cycles)
        self._send('VSWEEP!')
        if blocking:
            data = self._read_until_tag('</VSWEEP>')
            data = np.genfromtxt(StringIO(data), delimiter=",", comments='#')
            return data
        
    def _read_until_tag(self, tag):
        buff = []
        while True:
            line = self._read()
            buff.append(line)
            if line.find(tag) >= 0:
                return "\n".join(buff)

#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR
def get_interface(**kwargs):
    port = kwargs.pop('port')
    debug = kwargs.pop('debug', 'False')
    if debug == 'True':
        debug = True
    elif debug == 'False':
        debug = False
    else:
        raise ValueError("'debug' parameter must be either 'True' or 'False'")
    return Interface(port = port, debug = debug, **kwargs)
    
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    iface = Interface(port = "/dev/ttyUSB0")
