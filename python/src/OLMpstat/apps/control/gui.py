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
###############################################################################
# Module Constants
WINDOW_TITLE      = "OLMpstat Control"
WINDOW_TO_SCREENWIDTH_RATIO  = 0.9
WINDOW_TO_SCREENHEIGHT_RATIO = 0.9
WAIT_DELAY        = 100 #milliseconds
TEXT_BUFFER_SIZE  = 10*2**20 #ten megabytes
CV_FIGSIZE    = (6,5) #inches
CV_PLOT_STYLE = 'r-'
LOOP_DELAY        = 100 #milliseconds

BUTTON_WIDTH = 20
SECTION_PADY = 2
CONFIRMATION_TEXT_DISPLAY_TEXT_HEIGHT = 40
CONFIRMATION_TEXT_DISPLAY_TEXT_WIDTH  = 80

#Font Styles
FIELD_LABEL_FONT      = "Courier 10 normal"
HEADING_LABEL_FONT    = "Helvetica 14 bold"
SUBHEADING_LABEL_FONT = "Helvetica 10 bold"

SETTINGS_FILEPATH = os.path.expanduser("~/.olm_pstat_control_settings.db")

###############################################################################
#replacement dialog box, since Pmw.MessageDialog appears to mysteriously segfault
import Dialog

def launch_MessageDialog(title, message_text, buttons = ('OK',), bitmap='', default=0):
    d = tk.Dialog.Dialog(title=title, text = message_text, bitmap=bitmap, default=default, strings=buttons)
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

    def build_widgets(self):
        #FIXME bind some debugging keystrokes to the window
        #self._win.bind('<Control-f>', lambda e: self._app.)
        #-----------------------------------------------------------------------
        #build the left panel
        left_panel = tk.Frame(self._win)
        #voltage sweep controls
        tk.Label(left_panel, text="Voltage Sweep Controls:", font = HEADING_LABEL_FONT).pack(side='top',anchor="w")
        self.change_vsweep_settings_button = tk.Button(left_panel,
                                                       text    = 'Change Settings',
                                                       command = self.change_vsweep_settings,
                                                       width   = BUTTON_WIDTH)
        self.change_vsweep_settings_button.pack(side='top', anchor="sw")
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
#        self.vsweep_settings_dialog = VoltageSweepSettingsDialog(self.win)
#        self.vsweep_settings_dialog.withdraw()

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
        self.cv_plot_figure_widget = EmbeddedFigure(tab1, figsize = CV_FIGSIZE)
        self.cv_plot_figure_widget.pack(side='top',fill='both', expand='yes')
        self._update_cv_plot()
        #self.replot_raw_spectrum_button = tk.Button(tab1,text='Replot Spectrum',command = self.replot_raw_spectrum, state='disabled', width = BUTTON_WIDTH)
        #self.replot_raw_spectrum_button.pack(side='left',anchor="sw")
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
        self.text_display  = TextDisplayBox(right_panel,text_height=15, buffer_size = TEXT_BUFFER_SIZE)
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
        self.vsweep_capture_settings_button.configure(state="normal")
        self.vsweep_continually_button.configure(state="normal")
        #self.capture_stop_button.configure(state="normal")
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
        #frametype         = self.capture_settings_dialog.frametype_var.get()
        #exposure_time     = int(self.capture_settings_dialog.form['exposure_time'])
        self._app.print_comment("Running a voltage sweep:")
        #self.app.print_comment("\texposing for %d milliseconds..." % (exposure_time,))
        #self.app.voltage_sweep()
        self._win.after(LOOP_DELAY, self._wait_on_vsweep_loop)
        
    def _wait_on_vsweep_loop(self):
        voltage_sweep = self._app.load_controller('voltage_sweep')
        #read out all pending events
        while not voltage_sweep.event_queue.empty():
            event, info = voltage_sweep.event_queue.get()
            self.print_event(event,info)
#            if  event == "FILTER_SWITCHER_STARTED":
#                #filter is changing like in the 'opaque' frametype
#                self._update_filter_status(None)
        if voltage_sweep.thread_isAlive():
            #reschedule loop
            self._win.after(LOOP_DELAY,self._wait_on_vsweep_loop)
        else:
            #finish up
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
#                #filter is changing like in the 'opaque' frametype
#                self._update_filter_status(None)
#            elif event == "FILTER_SWITCHER_COMPLETED":
#               md = self.app.query_filter_status()
#               self._update_filter_status(md)
#            elif event == "IMAGE_CAPTURE_LOOP_SLEEPING":
#                time_left = info['time_left']
#                self.capture_time_left_field.setvalue("%d" % round(time_left))
#            elif event == "IMAGE_CAPTURE_EXPOSURE_COMPLETED":
#                #grab the image, comput the spectrum, then update them
#                I = info['image_array']
#                S = self.app.compute_raw_spectrum(I)
#                B = self.app.get_background_spectrum()
#                self._update_raw_spectrum_plot(S=S,B=B)
#                self._update_processed_spectrum_plot(S=S,B=B)
#                self._update_image(I)
#                self.replot_raw_spectrum_button.config(state='normal') #data can now be replotted
#                self.save_image_button.config(state='normal')      #data can now be exported
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
        self.cv_plot_template._has_been_plotted = False
#        S = self.app.get_raw_spectrum()
#        B = self.app.get_background_spectrum()
#        self._update_cv_plot(S=S,B=B)

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
    
    def _update_cv_plot(self, D = None):
        figure        = self.cv_plot_figure_widget.get_figure()
        plot_template = self.cv_plot_template
        title = "Current vs. Voltage"
        self.cv_plot_template.configure(title=title)
        if (not plot_template.has_been_plotted()):
            self._app.print_comment("Plotting the Current vs. Voltage.")
            figure.clear()
            Xs = []
            Ys = []
            styles = []
            labels = []
            if D is None:
                D = np.array([])
                Xs.append(np.arange(len(D)))
                Ys.append(D)
                styles.append(CV_PLOT_STYLE)
                labels.append("None")
            else:
                #get some metadata for label formatting
#                frametype = self.app.metadata['frametype']
#                exptime   = int(self.app.metadata['exposure_time'])
#                label     = "raw-%s, exptime = %d ms" % (frametype, exptime)
                Xs.append(np.arange(len(D)))
                Ys.append(D)
                styles.append(CV_PLOT_STYLE)
                labels.append(label)
            plot_template.plot(Xs, Ys, styles = styles, labels = labels, figure = figure)
            self.cv_plot_figure_widget.update()
        else:
            #get the plot line from the figure FIXME is there an easier way?
            axis = figure.axes[0]
            line0 = axis.lines[0]
            line0.set_ydata(S)
#            #get some metadata for label formatting
#            frametype = self.app.metadata['frametype']
#            exptime   = int(self.app.metadata['exposure_time'])
#            label     = "raw-%s, exptime = %d ms" % (frametype, exptime)
            line0.set_label(label)
            try:
                line1 = axis.lines[1]
                line1.set_label("background")
            except IndexError:
                pass
            axis.legend()
            self._app.print_comment("Updating Current vs. Voltage plot: %s" % label)
            #figure.axes[0].set_title(title)
            self.cv_plot_figure_widget.update()
