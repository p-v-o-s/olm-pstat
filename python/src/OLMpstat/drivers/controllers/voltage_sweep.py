"""
Controller to do voltage swept cyclic voltammetry using the OLM Potentiostat
device.

--------------------------------------------------------------------------------
Configuration:
            
v_start   - start voltage of sweep (default 0)
v_end     - ending voltage of sweep (default 1.5)
v_rate    - voltage ramp rate [Volts/sec] (default 0.25)
samp_rate - sample rate per second (default 10.0)
cycles    - number of cycles (default 1)
"""
###############################################################################
import sys, time, copy, traceback
from automat.core.hwcontrol.controllers.controller import Controller, AbortInterrupt, NullController
#Standard or substitute
OrderedDict = None
try:
    from collections import OrderedDict
except ImportError:
    from automat.substitutes.ordered_dict import OrderedDict
###############################################################################
DEFAULT_CONFIGURATION = OrderedDict([
    ('v_start', 0.0),
    ('v_end'  , 1.5),
    ('v_rate'   , 0.25),
    ('samp_rate', 10.0),
    ('cycles'   , 1),
    ('current_range_level',0),
    
])

SLEEP_TIME = 1.0 #seconds
COMMENT_SYMBOL = '#'
CSV_DELIMITER  = ','
###############################################################################
class Interface(Controller):
    def __init__(self,**kwargs):
        Controller.__init__(self, **kwargs)
            
    def shutdown(self):
        pstat = self.devices['pstat']
        pstat.shutdown()
             
    def main(self):
        try:
            cycles    = self.configuration['cycles']
            # START LOOP -------------------------------------------------
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['cycles']    = cycles
            self._send_event("VOLTAGE_SWEEP_LOOP_STARTED",info)
            i = 0
            while True:
                self._thread_abort_breakout_point()
                if  self._thread_check_stop_event() or (not cycles is None and i >= cycles):
                    # END NORMALLY ---------------------------------------
                    info = OrderedDict()
                    info['timestamp'] = time.time()
                    self._send_event("VOLTAGE_SWEEP_LOOP_STOPPED",info)
                    return
                # SWEEP & SAMPLE -----------------------------------------
                self.do_sweep(cycle_index = i)
                i += 1
                # REPEAT
        except (AbortInterrupt, Exception), exc:
            # END ABNORMALLY ---------------------------------------------
            self.abort_sweep()
            info = OrderedDict()
            info['timestamp'] = time.time()
            info['exception'] = exc
            if not isinstance(exc, AbortInterrupt):
                info['traceback'] = traceback.format_exc()
            self._send_event("VOLTAGE_SWEEP_LOOP_ABORTED",info)
        finally:
            # FINISH UP --------------------------------------------------
            self.reset()

        
    def do_sweep(self, cycle_index = None):
        pstat     = self.devices['pstat']
        v_start   = self.configuration['v_start']
        v_end     = self.configuration['v_end']
        v_rate    = self.configuration['v_rate']
        samp_rate = self.configuration['samp_rate']
        current_range_level = self.configuration['current_range_level']
        
        info = OrderedDict()
        info['timestamp'] = time.time()
        info['v_start']   = v_start
        if not cycle_index is None:
            info['cycle_index'] = cycle_index
        self._send_event("VOLTAGE_SWEEP_STARTED",info)
        
        #run sweep as a non-blocking procedure
        pstat.do_voltage_sweep(v_start = v_start,
                               v_end   = v_end,
                               v_rate  = v_rate,
                               samp_rate = samp_rate,
                               cycles = 1,
                               current_range_level = current_range_level,
                               blocking = False,
                              )
        #read past the header to the data
        pstat._read_until_tag('<CSV_DATA>')
        #parse each line into an event as it comes in
        while True:
            self._thread_abort_breakout_point()
            line = pstat._read()
            if not line.startswith(COMMENT_SYMBOL):  #data record
                control_voltage, WEtoRE_voltage, WE_current = line.split(CSV_DELIMITER)
                info = OrderedDict()
                info['timestamp'] = time.time()
                info['control_voltage'] = float(control_voltage)
                info['WEtoRE_voltage']  = float(WEtoRE_voltage)
                info['WE_current']      = float(WE_current)
                self._send_event("VOLTAGE_SWEEP_SAMPLE",info)
            elif line.find('</CSV_DATA>') >= 0:      #ending comment
                info = OrderedDict()
                info['timestamp'] = time.time()
                self._send_event("VOLTAGE_SWEEP_COMPLETED", info)
                return
            else:                                    #other comments
                info = OrderedDict()
                info['timestamp'] = time.time()
                info['msg']       = line
                self._send_event("VOLTAGE_SWEEP_COMMENT", info)
                
    def abort_sweep(self, cycle_index = None):
        pstat = self.devices['pstat']
        pstat.abort_sweep()
        info = OrderedDict()
        info['timestamp'] = time.time()
        self._send_event("VOLTAGE_SWEEP_ABORT",info)
   
#------------------------------------------------------------------------------
# INTERFACE CONFIGURATOR
def get_interface(**kwargs):
    interface_mode = kwargs.pop('interface_mode','threaded')
    if   interface_mode == 'threaded':
        return Interface(**kwargs)
    else:
        raise ValueError("interface_mode '%s' is not valid" % interface_mode)
            
###############################################################################
# TEST CODE - Run the Controller, collect events, and plot
###############################################################################
# FIXME
if __name__ == "__main__":
    pass

