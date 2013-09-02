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


BAUDRATE = 115200
EOL  = "\n"

###############################################################################
class Interface(Device, SerialCommunicationsMixIn):
    def __init__(self, port, **kwargs):
        debug = kwargs.pop('debug', False)
        self._debug = debug
        #initialize GPIB communication
        SerialCommunicationsMixIn.__init__(self, port, **kwargs)
        
    def reset(self):
        self._send("*RST")
        self._read_until_tag("</INIT>")
        
    def get_status(self):
        self._send("STATUS?")
        resp = self._read_until_tag("</STATUS>")
        info = yaml.load(resp)
        return info
        
    def do_voltage_sweep(self,
                         v_start, v_end, v_rate,
                         samp_rate = 10.0,
                         cycles = 1,
                        ):
        v_start = float(v_start)
        v_end   = float(v_end)
        v_rate  = float(v_rate)
        cycles  = int(cycles)
        self._send("VSWEEP.START %f" % v_start)
        self._send("VSWEEP.END %f" % v_end)
        self._send("VSWEEP.RAMP %f" % v_rate)
        self._send("VSWEEP.SAMPLE %f" % samp_rate)
        self._send("VSWEEP.CYCLES %d" % cycles)
        self._send('VSWEEP!')
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
    return Interface(port = port, **kwargs)
    
###############################################################################
# TEST CODE
###############################################################################
if __name__ == "__main__":
    iface = Interface(port = "/dev/ttyUSB0")
