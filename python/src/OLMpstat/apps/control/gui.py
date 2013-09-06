###############################################################################
#Standard Python provided
import os, time, datetime, shelve, re
import Tkinter as tk
import ttk
#Standard or substitute
OrderedDict = None
try:
    from collections import OrderedDict
except ImportError:
    from automat.substitutes.ordered_dict import OrderedDict
#3rd party packages
import Pmw
import numpy as np
from FileDialog import SaveFileDialog, LoadFileDialog
#Automat framework provided
from automat.services.gui import GUIBase
from automat.core.gui.text_widgets           import TextDisplayBox
from automat.core.gui.pmw_custom.entry_form  import EntryForm
from automat.core.gui.pmw_custom.validation  import Validator
from automat.core.plotting.tk_embedded_plots import EmbeddedFigure
from automat.system_tools.daemonize          import ignore_KeyboardInterrupt, notice_KeyboardInterrupt
#OLMpstat framework provided
from OLMpstat.core.plotting.templates        import CurrentVoltagePlot
#application local
from vsweep_settings_dialog import VoltageSweepSettingsDialog
###############################################################################
# Module Constants
LOOP_DELAY = 100 #milliseconds
WAIT_DELAY = 100 #milliseconds
VSWEEP_LOOP_DELAY = 1 #milliseconds

WINDOW_TITLE      = "OLMpstat Control"
WINDOW_TO_SCREENWIDTH_RATIO  = 0.9
WINDOW_TO_SCREENHEIGHT_RATIO = 0.9

BUTTON_WIDTH = 20
SECTION_PADY = 2

TEXTBOX_WIDTH        = 20  #characters
TEXTBOX_BUFFER_SIZE  = 10*2**20 #ten megabytes

CONFIRMATION_TEXT_DISPLAY_TEXT_HEIGHT = 40
CONFIRMATION_TEXT_DISPLAY_TEXT_WIDTH  = 80

CV_PLOT_TITLE = "Current vs. Voltage"
CV_PLOT_FIGSIZE    = (6,5) #inches
CV_PLOT_STYLES = ['r.-',
                  'g.-',
                  'b.-',
                  'c.-',
                  'y.-',
                  'm.-',
                  'k.-',
                  'r.--',
                  'g.--',
                  'b.--',
                  'c.--',
                  'y.--',
                  'm.--',
                  'k.--']

#Font Styles
FIELD_LABEL_FONT      = "Courier 10 normal"
HEADING_LABEL_FONT    = "Helvetica 14 bold"
SUBHEADING_LABEL_FONT = "Helvetica 10 bold"

SETTINGS_FILEPATH = os.path.expanduser("~/.olm_pstat_control_settings.db")

###############################################################################
#replacement dialog box, since Pmw.MessageDialog appears to mysteriously segfault
import Dialog

def launch_MessageDialog(title,
                         message_text,
                         buttons = ('OK',),
                         bitmap = '',
                         default = 0,
                         ):
    d = tk.Dialog.Dialog(title = title,
                         text = message_text,
                         bitmap = bitmap,
                         default = default,
                         strings = buttons)
    return buttons[d.num]
      
###############################################################################
class GUI(GUIBase):
    def build_window(self):
        GUIBase.build_window(self)
        #now size the window and center it
        sw = self._win.winfo_screenwidth()
        sh = self._win.winfo_screenheight()
        w  = sw*WINDOW_TO_SCREENWIDTH_RATIO
        h  = sh*WINDOW_TO_SCREENHEIGHT_RATIO
        x = (sw - w)/2
        y = (sh - h)/2
        self._win.geometry("%dx%d+%d+%d" % (w,h,x,y))
        self._cv_plot_Xs = []
        self._cv_plot_Ys = []
        self._cv_plot_labels = []

    def build_widgets(self):
        #FIXME bind some debugging keystrokes to the window
        #self._win.bind('<Control-f>', lambda e: self._app.)
        #-----------------------------------------------------------------------
        #build the left panel
        left_panel = tk.Frame(self._win)
        #voltage sweep controls
        tk.Label(left_panel, text="Voltage Sweep Controls:", font = HEADING_LABEL_FONT).pack(side='top',anchor="w")
        self.vsweep_settings_button = tk.Button(left_panel,
                                                text    = 'Change Settings',
                                                command = self.change_vsweep_settings,
                                                width   = BUTTON_WIDTH)
        self.vsweep_settings_button.pack(side='top', anchor="sw")
        self.vsweep_once_button = tk.Button(left_panel,
                                            text   = 'Run Once',
                                            command = self.vsweep_once,
                                            width   = BUTTON_WIDTH)
        self.vsweep_once_button.pack(side='top', anchor="nw")
        self.vsweep_continually_button = tk.Button(left_panel,
                                                   text    = 'Run Continually',
                                                   command = self.vsweep_continually,
                                                   width   = BUTTON_WIDTH)
        self.vsweep_continually_button.pack(side='top', anchor="nw")
        self.vsweep_stop_button = tk.Button(left_panel,
                                            text    = 'Stop',
                                            command = self.vsweep_stop,
                                            state   = 'disabled',
                                            width   = BUTTON_WIDTH)
        self.vsweep_stop_button.pack(side='top', anchor="nw")
       
        #build the capture settings dialog
        self.vsweep_settings_dialog = VoltageSweepSettingsDialog(self._win)
        self.vsweep_settings_dialog.withdraw()

        #finish the left panel
        left_panel.pack(fill='y',expand='no',side='left', padx = 10)
        #-----------------------------------------------------------------------
        #build the middle panel - a tabbed notebook
        mid_panel = tk.Frame(self._win)
        #mid_panel.pack(fill='both', expand='yes',side='left')
        nb        = ttk.Notebook(mid_panel)
        nb.pack(fill='both', expand='yes',side='right')
        tab1 = tk.Frame(nb)
        tab1.pack(fill='both', expand='yes',side='right')
        nb.add(tab1, text = "Current vs. Voltage")
        #create an tk embedded figure for the current vs. voltage display
        self.cv_plot_template = CurrentVoltagePlot()
        self.cv_plot_template.configure(title = CV_PLOT_TITLE)
        self.cv_plot_figure_widget = EmbeddedFigure(tab1, figsize = CV_PLOT_FIGSIZE)
        self.cv_plot_figure_widget.pack(side='top',fill='both', expand='yes')
        self._update_cv_plot()  #make an empty plot
        self.replot_cv_button = tk.Button(tab1,text='Replot',command = self.replot_cv, state='normal', width = BUTTON_WIDTH)
        self.replot_cv_button.pack(side='left',anchor="sw")
        self.clear_cv_button = tk.Button(tab1,text='Clear',command = self.clear_data, state='normal', width = BUTTON_WIDTH)
        self.clear_cv_button.pack(side='left',anchor="sw")
        self.export_data_button = tk.Button(tab1,
                                            text    ='Export Data',
                                            command = self.export_data,
                                            state   = 'disabled',
                                            width   = BUTTON_WIDTH)
        self.export_data_button.pack(side='left',anchor="sw")
        #finish builing the middle pannel
        mid_panel.pack(fill='both', expand='yes',side='left')
        #-----------------------------------------------------------------------
        #build the right panel
        right_panel = tk.Frame(self._win)
        
        #Status variable display
        tk.Label(right_panel, pady = SECTION_PADY).pack(side='top',fill='x', anchor="nw")
        tk.Label(right_panel, text="Status:", font = HEADING_LABEL_FONT).pack(side='top',anchor="w")
        #self.condition_fields = ConditionFields(right_panel)
        #self.condition_fields.pack(side='top', anchor="w", expand='no')
        
        # Events text display
        tk.Label(right_panel, pady = SECTION_PADY).pack(side='top',fill='x', anchor="nw")
        tk.Label(right_panel, text="Events Monitoring:", font = HEADING_LABEL_FONT).pack(side='top',anchor="w")
        self.text_display  = TextDisplayBox(right_panel,
                                            text_width  = TEXTBOX_WIDTH,
                                            buffer_size = TEXTBOX_BUFFER_SIZE,
                                            )
        self.text_display.pack(side='top',fill='both',expand='yes')
        #finish building the right panel
        right_panel.pack(fill='both', expand='yes',side='right', padx = 10)
         

    def load_settings(self):
        if os.path.exists(SETTINGS_FILEPATH):
            self._app.print_comment("loading from settings file '%s'" % SETTINGS_FILEPATH)
            settings = shelve.open(SETTINGS_FILEPATH)
            #self.vsweep_settings_dialog.frametype_var.set(FRAMETYPE_DEFAULT) #always load this as default
            #self.vsweep_settings_dialog.form['exposure_time']     = settings.get('exposure_time'    , EXPOSURE_TIME_DEFAULT)
            settings.close()
        else:
            self._app.print_comment("failed to find settings file '%s'" % SETTINGS_FILEPATH)
                  
    def cache_settings(self):
        self._app.print_comment("caching to settings file '%s'" % SETTINGS_FILEPATH)
        settings = shelve.open(SETTINGS_FILEPATH)
        #settings['exposure_time']     = self.vsweep_settings_dialog.form['exposure_time']
        settings.close()
    
    def busy(self):
        self.disable_control_buttons()
        self._win.config(cursor="watch")
        
    def not_busy(self):
        self.enable_control_buttons()
        self._win.config(cursor="")

    def print_to_text_display(self, text, eol='\n'):
        try:
            self.text_display.print_text(text, eol=eol)
        except AttributeError: #ignore missing text display widget
            pass

    def print_event(self, event, info = {}):
        buff = ["%s:" % event]
        for key,val in info.items():
            buff.append("%s: %s" % (key,val))
        buff = "\n".join(buff)
        self.print_to_text_display(buff)
        
    def disable_control_buttons(self):
        self.vsweep_settings_button.configure(state="disabled")
        self.vsweep_continually_button.configure(state="disabled")
        #self.capture_stop_button.configure(state="disabled")
        self.vsweep_once_button.configure(state="disabled")
        
    def enable_control_buttons(self):
        self.vsweep_settings_button.configure(state="normal")
        self.vsweep_continually_button.configure(state="normal")
        #self.vsweep_stop_button.configure(state="normal")
        self.vsweep_once_button.configure(state="normal")

    def change_vsweep_settings(self):
        choice = self.vsweep_settings_dialog.activate()
        if choice == "OK":
            self._app.print_comment("changing voltage sweep settings...")

    def vsweep_once(self):
        #disable all the control buttons, except the stop button
        self.vsweep_once_button.config(bg='green', relief='sunken')
        self.disable_control_buttons()
        self.vsweep_stop_button.config(state='normal')
        #get parameters
        v_start   = float(self.vsweep_settings_dialog.form['v_start'])
        v_end     = float(self.vsweep_settings_dialog.form['v_end'])
        v_rate    = float(self.vsweep_settings_dialog.form['v_rate'])
        samp_rate = float(self.vsweep_settings_dialog.form['samp_rate'])
        cycles    = int(self.vsweep_settings_dialog.form['cycles'])
        current_range_level = self.vsweep_settings_dialog.current_range_level_var.get()
        current_range_level, _ = current_range_level.split(",")
        current_range_level = int(current_range_level)
        self._app.print_comment("Running a voltage sweep:")
        self._app.print_comment("    v_start: %0.2f" % (v_start,))
        self._app.print_comment("    v_end: %0.2f" % (v_end,))
        self._app.print_comment("    v_rate: %0.2f" % (v_rate,))
        self._app.print_comment("    samp_rate: %0.2f" % (samp_rate,))
        self._app.print_comment("    cycles: %0.2f" % (cycles,))
        #start the voltage sweep, SHOULD NOT BLOCK!
        self._app.start_voltage_sweep(v_start   = v_start,
                                      v_end     = v_end,
                                      v_rate    = v_rate,
                                      samp_rate = samp_rate,
                                      cycles    = cycles,
                                      current_range_level = current_range_level,
                                     )
        self._win.after(LOOP_DELAY, self._wait_on_vsweep_loop)
        
    def _wait_on_vsweep_loop(self):
        voltage_sweep = self._app._load_controller('voltage_sweep')
        #read out all pending events
        while not voltage_sweep.event_queue.empty():
            event, info = voltage_sweep.event_queue.get()
            self.print_event(event,info)
            if  event == "VOLTAGE_SWEEP_SAMPLE":
                self._app._append_vsweep_data_record(info['control_voltage'],
                                                     info['WEtoRE_voltage'],
                                                     info['WE_current'],
                                                    )
                #use new data to update the plot
                V1 = self._app._vsweep_dataset['control_voltage']
                V2 = self._app._vsweep_dataset['WEtoRE_voltage']
                I  = self._app._vsweep_dataset['WE_current']
                self._update_cv_plot(X_now = V2, Y_now = I)
        if voltage_sweep.thread_isAlive():
            #reschedule loop
            self._win.after(VSWEEP_LOOP_DELAY,self._wait_on_vsweep_loop)
        else:
            #finish up
            #cache the data for the plot
            V1 = self._app._vsweep_dataset['control_voltage']
            V2 = self._app._vsweep_dataset['WEtoRE_voltage']
            I  = self._app._vsweep_dataset['WE_current']
            self._cv_plot_Xs.append(V2)
            self._cv_plot_Ys.append(I)
            #styles = []
            new_label = "Trial %d" % (len(self._cv_plot_labels) + 1,)
            self._cv_plot_labels.append(new_label)
            self.replot_cv()
            #self.not_busy()
            #re-enable all the buttons, except the stop button
            self.enable_control_buttons()
            self.vsweep_once_button.config(bg='light gray', relief='raised')
            self.vsweep_stop_button.config(state='disabled')
            self._app.print_comment("voltage sweep completed")
            #self.replot_raw_spectrum_button.config(state='normal') #data can now be replotted
            self.export_data_button.config(state='normal') #data can now be exported
     
    def vsweep_continually(self):
        #disable all the control buttons, except the stop button
        self.vsweep_continually_button.config(state='disabled', bg='green', relief="sunken")
        self.disable_control_buttons()
        self.vsweep_stop_button.config(state='normal')
        self._vsweep_mode = "continual"
        #get parameters
        #frametype         = self.vsweep_settings_dialog.frametype_var.get()
        #exposure_time     = float(self.vsweep_settings_dialog.form['exposure_time'])
        #set up the image capture controller in loop mode
        voltage_sweep = self._app.load_controller('voltage_sweep')
        #voltage_sweep.set_configuration(frametype         = frametype,
        #                               )
        #refresh the metdata
        self._app.query_metadata()
        self._app.print_comment("Starting voltage sweep continually loop:")
        voltage_sweep.start() #should not block
        #schedule loop
        self._vsweep_continually_loop()

    def _vsweep_continually_loop(self):
        voltage_sweep = self._app.load_controller('voltage_sweep')
        #read out all pending events
        while not voltage_sweep.event_queue.empty():
            event, info = voltage_sweep.event_queue.get()
            self.print_event(event,info)
#            if   event == "FILTER_SWITCHER_STARTED":
#            elif event == "IMAGE_CAPTURE_EXPOSURE_COMPLETED":
#                #grab the image, comput the spectrum, then update them
        #reschedule loop
        if voltage_sweep.thread_isAlive():  #wait for the capture to finish, important!
            self._vsweep_after_id = self._win.after(LOOP_DELAY, self._vsweep_continually_loop)
        else:
            #finish up
            #enable all the buttons, except the stop button
            self.enable_control_buttons()
            self.vsweep_continually_button.config(state='normal', bg='light gray', relief = 'raised')
            #data can now be exported
            self.export_data_button.config(state='normal')
            #do not reschedule loop

    def vsweep_stop(self):
        self.vsweep_stop_button.config(state='disabled')
        voltage_sweep = self._app.load_controller('voltage_sweep')
        #force it to stop right now instead of finishing sleep
        voltage_sweep.abort()
        if not self._vsweep_after_id is None:
            #cancel the next scheduled loop time
            self._win.after_cancel(self._vsweep_after_id)
            #then enter the loop one more time to clean up
            self._vsweep_continually_loop()
        self._vsweep_mode = None
    
    def replot_cv(self):
        voltage_sweep = self._app._load_controller('voltage_sweep')
        figure = self.cv_plot_figure_widget.get_figure()
        figure.clear()
        self.cv_plot_template._has_been_plotted = False
        #check to see if the current trial is still running
        if voltage_sweep.thread_isAlive():
            #if so pass in the current trial data
            V1 = self._app._vsweep_dataset['control_voltage']
            V2 = self._app._vsweep_dataset['WEtoRE_voltage']
            I  = self._app._vsweep_dataset['WE_current']
            self._update_cv_plot(X_now = V2, Y_now = I)
        else:
            #otherwise just the completed data sets (i.e., avoid redundancy of last set)
            self._update_cv_plot()

    def export_data(self):
        self._app.print_comment("Exporting data...")
        dt_now = datetime.datetime.utcnow()
        dt_now_str = dt_now.strftime("%Y-%m-%d-%H_%M_%S")
        #get some metadata for title
        v_start = float(self._app.last_vsweep_metadata['v_start'])
        v_end   = float(self._app.last_vsweep_metadata['v_end'])
        default_filename = "%s_vsweep_%0.2f_to_%0.2fV.csv" % (dt_now_str,v_start,v_end)
        fdlg = SaveFileDialog(self.win,title="Save Voltage Sweep Data")
        userdata_path = self._app.config['paths']['data_dir']

        filename = fdlg.go(dir_or_file = userdata_path,
                           pattern="*.csv",
                           default=default_filename,
                           key = None
                          )
        if filename:
            self._app.export_data(filename)
        self._app.print_comment("finished")
        
    def clear_data(self):
        self._cv_plot_Xs = []
        self._cv_plot_Ys = []
        self._cv_plot_labels = []
        self.replot_cv()
    
    def _update_cv_plot(self, X_now = None, Y_now = None):
        figure        = self.cv_plot_figure_widget.get_figure()
        plot_template = self.cv_plot_template
        
        if not plot_template.has_been_plotted():
            self._app.print_comment("Plotting the Current vs. Voltage.")
            Xs = self._cv_plot_Xs[:] #make copy to not mutate!
            if not X_now is None:
                Xs.append(X_now)
            else:
                Xs.append([])
            Ys = self._cv_plot_Ys[:] #make copy to not mutate!
            if not Y_now is None:
                Ys.append(Y_now)
            else:
                Ys.append([])
            #styles = CV_PLOT_STYLES
            labels = self._cv_plot_labels + ['Current Trial']
            plot_template.plot(Xs, Ys,
                               #styles = styles,
                               labels = labels,
                               figure = figure
                              )
            self.cv_plot_figure_widget.update()
        else:
            self._app.print_comment("Updating Current vs. Voltage plot.")
            #get the plot line from the figure FIXME is there an easier way?
            axis = figure.axes[0]
            last_line = axis.lines[-1]
            if not X_now is None:
                last_line.set_xdata(X_now)
            if not Y_now is None:
                last_line.set_ydata(Y_now)
            self.cv_plot_figure_widget.update()
#            #FIXME cook up a label
#            #axis.legend()
#            #self._app.print_comment("Updating Current vs. Voltage plot: %s" % label)
#            self._app.print_comment("Updating Current vs. Voltage plot.")
#            #figure.axes[0].set_title(title)
#            self.cv_plot_figure_widget.update()
