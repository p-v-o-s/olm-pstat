###############################################################################
#Standard Python
#Standard or substitute
OrderedDict = None
try:
    from collections import OrderedDict
except ImportError:
    from automat.substitutes.ordered_dict import OrderedDict
#3rd party
import numpy as np
#Automat framework provided
from automat.core.data_processing.datasets import DataSet
#OLMpstat framework provided
#local
###############################################################################
# Module Constants
FIELD_NAMES = ['control_voltage',
               'WEtoRE_voltage',
               'WE_current',
              ]

###############################################################################
class VoltageSweepDataSet(DataSet):
    def __init__(self,
                 control_voltage = None,
                 WEtoRE_voltage  = None,
                 WE_current      = None,
                 metadata = None
                ):
        #convert fields to ndarray objects
        if control_voltage is None:
           V1 = np.array([], dtype='float64')
        else:
           V1 = np.array(control_voltage, dtype='float64')
        
        if WEtoRE_voltage is None:
           V2 = np.array([], dtype='float64')
        else:
           V2 = np.array(WEtoRE_voltage, dtype='float64')
        
        if WE_current is None:
           I = np.array([], dtype='float64')
        else:
           I = np.array(WE_current, dtype='float64')
           
        fields  = [V1,V2,I]
        names   = FIELD_NAMES
        if metadata is None:
            metadata = OrderedDict()
        DataSet.__init__(self, fields, names=names, metadata=metadata)
    #--------------------------------------------------------------------------
    # CLASS METHODS
    @classmethod
    def load(cls, filename):
        base, ext = os.path.splitext(filename)
        if   ext == ".csv":
            return cls.from_csv(filename)
        elif ext == ".db":
            return cls.from_shelf(filename)
        elif ext == ".hd5":
            raise NotImplementedError("HDF5 formatting is not ready, please check back later!")
        else:
            raise ValueError("the filename extension '%s' was not recognized, it must end with: .csv, .db, or .hd5" % ext)
        
    @classmethod
    def from_dict(cls, spec):
        """Class factory function which builds a SpectrumDataSet obj from 
           a dictionary specification.
        """
        data = spec['data']
        obj = cls( control_voltage = data['control_voltage'],
                   WEtoRE_voltage  = data['control_voltage'],
                   WE_current      = data['control_voltage'],
                 )
        return obj
        
    @classmethod
    def from_csv(cls, filename):
        """ Class factory function: load and parse a YES O2AB CSV 
            (comma seperated values, with metadata) format and construct
            a SpectrumDataSet object.
        """
        raise NotImplementedError
        spec = voltage_sweep_csv_parser.load(filename)
        return cls.from_dict(spec)
