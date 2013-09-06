import Tkinter as tk
import Pmw

#Automat framework provided
from automat.core.gui.pmw_custom.validation import Validator
from automat.core.gui.pmw_custom.entry_form import EntryForm
###############################################################################
TITLE = "Change Voltage Sweep Settings"
ENTRY_WIDTH      = 6
FIELD_LABEL_FONT = "Courier 10 normal"

V_START_DEFAULT  = 0.0
V_START_MIN      = -1.5
V_START_MAX      =  1.5
V_END_DEFAULT    = 1.0
V_END_MIN        = -1.5
V_END_MAX        =  1.5
V_RAMP_DEFAULT   = 0.25  #volts per second
V_RAMP_MIN       = 0.01
V_RAMP_MAX       = 1.0
SAMPRATE_DEFAULT = 10.0    #samps per second
SAMPRATE_MIN     = 0.1
SAMPRATE_MAX     = 100.0
CYCLES_DEFAULT   = 1
CYCLES_MIN       = 1
CYCLES_MAX       = 999
CURRENT_RANGE_LEVEL_DEFAULT = '0, <   6 mA'
MENUBUTTON_WIDTH = 12
###############################################################################
class VoltageSweepSettingsDialog(Pmw.Dialog):
    def __init__(self,
                 parent = None,
                 ):
                  
        #set up dialog windows
        Pmw.Dialog.__init__(self,
                            parent = parent,
                            title = TITLE, 
                            buttons = ('OK',),
                            defaultbutton = 'OK',
                           )
        frame = self.interior()
        #form widget for a bunch of entries with validation and conversion
        form = EntryForm(frame)
        form.new_field('v_start',
                       labelpos    = 'w',
                       label_text  = "      Start Voltage (V):",
                       label_font  = FIELD_LABEL_FONT,
                       entry_width = ENTRY_WIDTH,
                       value       = V_START_DEFAULT,
                       validate    = Validator(_min = V_START_MIN,
                                               _max = V_START_MAX,
                                               converter = float)
                      )
        form.new_field('v_end',
                       labelpos    = 'w',
                       label_text  = "        End Voltage (V):",
                       label_font  = FIELD_LABEL_FONT,
                       entry_width = ENTRY_WIDTH,
                       value       = V_END_DEFAULT,
                       validate    = Validator(_min = V_END_MIN,
                                               _max = V_END_MAX,
                                               converter = float)
                      )
        form.new_field('v_rate',
                       labelpos    = 'w',
                       label_text  = "Voltage Ramp Rate (V/s):",
                       label_font  = FIELD_LABEL_FONT,
                       entry_width = ENTRY_WIDTH,
                       value       = V_RAMP_DEFAULT,
                       validate    = Validator(_min = V_RAMP_MIN,
                                               _max = V_RAMP_MAX,
                                               converter = float)
                      )
        form.new_field('samp_rate',
                       labelpos    = 'w',
                       label_text  = "        Sample Rate (V):",
                       label_font  = FIELD_LABEL_FONT,
                       entry_width = ENTRY_WIDTH,
                       value       = SAMPRATE_DEFAULT,
                       validate    = Validator(_min = SAMPRATE_MIN,
                                               _max = SAMPRATE_MAX,
                                               converter = float)
                      )
        form.new_field('cycles',
                       labelpos    = 'w',
                       label_text  = "       Number of Cycles:",
                       label_font  = FIELD_LABEL_FONT,
                       entry_width = ENTRY_WIDTH,
                       value       = CYCLES_DEFAULT,
                       validate    = Validator(_min = CYCLES_MIN,
                                               _max = CYCLES_MAX,
                                               converter = int)
                      )
        form.pack(expand='yes', fill='both')
        self.form = form
        
        #number of choices for frametype
        self.current_range_level_var = tk.StringVar(value=CURRENT_RANGE_LEVEL_DEFAULT)
        self.current_range_level_optionmenu = Pmw.OptionMenu(frame,
                                                   labelpos = 'w',
                                                   label_text = 'Current Range Level:',
                                                   label_font  = FIELD_LABEL_FONT,
                                                   menubutton_textvariable = self.current_range_level_var,
                                                   items = ['0, <   6 mA',
                                                            '1, < 600 uA',
                                                            '2, <  60 uA',
                                                            '3, <   6 uA',
                                                            '4, < 600 nA',
                                                           ],
                                                   menubutton_width = MENUBUTTON_WIDTH,
                                                  )
        self.current_range_level_optionmenu.pack(expand='no',fill='x')
        
    def activate(self):
        "override activate to construct and send back the action and the new values"
        action = Pmw.Dialog.activate(self)
        return action
###############################################################################
 

###############################################################################
# TEST CODE - FIXME
###############################################################################
if __name__ == "__main__":
    

    # Initialise Tkinter and Pmw.
    import Tkinter    
    import Pmw
    #create a test window    
    root = Pmw.initialise()    
    
