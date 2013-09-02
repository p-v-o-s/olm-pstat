import numpy as np
import pylab
import serial, yaml
from StringIO import StringIO

BAUDRATE = 9600
EOL  = "\n"


class Potentiostat(object):
    def __init__(self, port, baudrate = BAUDRATE, eol = EOL, debug = False):
        self._ser = serial.Serial(port, baudrate = baudrate)
        self._eol = eol
        self.debug = debug
        
    def reset(self):
        self._send_command("*RST")
        self._read_until_tag("</INIT>")
        
    def get_status(self):
        self._send_command("STATUS?")
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
        self._send_command("VSWEEP_START %f" % v_start)
        self._send_command("VSWEEP_END %f" % v_end)
        self._send_command("VSWEEP_RAMP %f" % v_rate)
        self._send_command("VSWEEP_SAMPLE %f" % samp_rate)
        self._send_command("VSWEEP_CYCLES %d" % cycles)
        self._send_command('VSWEEP')
        data = self._read_until_tag('</VSWEEP>')
        data = np.genfromtxt(StringIO(data), delimiter=",",comments='#')
        return data
    
    def _send_command(self, cmd):
        cmd = cmd.strip() + self._eol
        if self.debug:
            print "--> " + cmd,
        self._ser.write(cmd)
        
    def _readline(self):
        line = self._ser.readline().strip('\r\n')
        if self.debug:
            print "<-- " + line
        return line
        
    def _exchange_command(self, cmd):
        self._send_command(cmd)
        resp = self._readline()
        return resp
        
    def _read_until_tag(self, tag):
        buff = []
        while True:
            line = self._readline()
            buff.append(line)
            if line.find(tag) >= 0:
                return "\n".join(buff)
