################################################################################
#Dependencies
#standard python
import time
#Standard or substitute
OrderedDict = None
try:
    from collections import OrderedDict
except ImportError:
    from automat.substitutes.ordered_dict import OrderedDict
#Automat framework provided
from automat.services.application import ApplicationBase
#3rd party hardware vendor, install from Internet
import numpy as np
#OLMpstat framework provided
from OLMpstat.core.data_processing.voltage_sweep_dataset import VoltageSweepDataSet
#package local
################################################################################
#Module Constants
USED_CONTROLLERS = []
################################################################################
class Application(ApplicationBase):
    def __init__(self, skip_test = False, **kwargs):
        kwargs['used_controllers'] = USED_CONTROLLERS
        ApplicationBase.__init__(self, **kwargs)
        self._vsweep_dataset = VoltageSweepDataSet()
        
    def initialize(self, used_controllers = USED_CONTROLLERS):
        ApplicationBase.initialize(self, used_controllers = used_controllers)
        
    def start_voltage_sweep(self,
                            v_start,
                            v_end,
                            v_rate,
                            samp_rate = 10.0,
                            cycles = 1,
                            current_range_level = 0,
                            #blocking = True,
                           ):
        voltage_sweep = self._load_controller('voltage_sweep')
        voltage_sweep.set_configuration(v_start = v_start,
                                        v_end = v_end,
                                        v_rate = v_rate,
                                        samp_rate = samp_rate,
                                        cycles = cycles,
                                        current_range_level = current_range_level,
                                        )
        #creat new or overwrite the last dataset
        md = OrderedDict()
        md['start_timestamp'] = time.time()
        md['v_start']         = v_start
        md['v_end']           = v_end
        md['v_rate']          = v_rate
        md['samp_rate']       = samp_rate
        md['cycles']          = cycles
        md['current_range_level'] = current_range_level
        self._vsweep_dataset = VoltageSweepDataSet(metadata = md)
        voltage_sweep.start() #this should start a non-blocking thread
        
    def _append_vsweep_data_record(self,
                                   control_voltage,
                                   WEtoRE_voltage,
                                   WE_current,
                                  ):
        self._vsweep_dataset.append_record(#this needs a sequence
                                           (control_voltage,
                                            WEtoRE_voltage,
                                            WE_current)
                                          )
                                          
    def export_data(self, filename):
        if   filename.endswith(".csv"):
            self._vsweep_dataset.to_csv_file(filename)
        elif filename.endswith(".db"):
            self._vsweep_dataset.to_shelf(filename)
        elif filename.endswith(".hd5"):
            raise NotImplementedError("HDF5 formatting is not ready, please check back later!")
        else:
            raise ValueError("the filename extension was not recognized, it must end with: .csv, .db, or .hd5")
