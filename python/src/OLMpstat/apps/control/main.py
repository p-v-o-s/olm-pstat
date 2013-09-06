################################################################################
#Dependencies
#standard python
#Automat framework provided
from automat.services.errors import handleCrash
#OLMpstat framework provided
import OLMpstat.pkg_info
#3rd party hardware vendor, install from Internet
################################################################################
#Module Constants
################################################################################
@handleCrash
def main():
    #---------------------------------------------------------------------------
    import sys, argparse
    #application local
    from gui         import GUI
    from application import Application
    #---------------------------------------------------------------------------
    #parse command line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument("--skip-test",
                        default = False,
                        action  = 'store_true',
                        help    = "skip over device tests",
                       )
    parser.add_argument("--no-detach",
                        dest    = "detach",
                        default = True,
                        action  = 'store_false',
                        help    = "remain bound to terminal session",
                       )
    parser.add_argument("--ignore-device-errors",
                        dest    = "ignore_device_errors",
                        default = False,
                        action  = 'store_true',
                        help    = "ignore initial device errors"
                       )
    args = parser.parse_args()
      
    #initialize the control application
    app = Application(skip_test = args.skip_test,
                      ignore_device_errors = args.ignore_device_errors,
                     )
    #parse and loads the configuration objects
    app.load(config_filepath = OLMpstat.pkg_info.platform['config_filepath'])
    #initialize the controllers
    app.initialize()
    if args.detach:
        #detach the process from its controlling terminal
        from automat.system_tools.daemonize import detach
        app.print_comment("Process Detached.")
        app.print_comment("You may now close the terminal window...")
        detach()
    #start the graphical interface
    gui = GUI(app)
    #give the app the ability to print to the GUI's textbox
    app.setup_textbox_printer(gui.print_to_text_display)
    #launch the GUI
    gui.load()
    gui.launch()

if __name__ == "__main__":
    main()
