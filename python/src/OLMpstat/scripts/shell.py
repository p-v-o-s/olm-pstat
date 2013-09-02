import time
try:
    #first try new style >= 0.12 interactive shell
    from IPython.frontend.terminal.embed import InteractiveShellEmbed as IPYTHON_SHELL
except ImportError:
    #substitue old-style interactive shell
    from IPython.Shell import IPShellMatplotlib as IPYTHON_SHELL

from automat.core.hwcontrol.config.configuration import Configuration

import OLMpstat.pkg_info

__BANNER  = ['*'*80,
             '* OLMpstat Shell',
             '*     author: cversek@pvos.org',
             '*'*80]
__BANNER  = '\n'.join(__BANNER)

DEFAULT_SEARCHPATHS = ['.', OLMpstat.pkg_info.platform['config_filedir']]
DEFAULT_INTERFACE_MODE = 'interactive'

class Application:
    def __init__(self, commands = None):
        #self.searchpaths = searchpaths
        self.config = None
        self.user_ns  = {}
        if commands is None:
            commands = {}
        self.commands = commands
        
    def load(self):
        self._load_config()
        self._load_all_devices()
        self._load_all_controllers()
        
    def _load_config(self):
        config_filepath = OLMpstat.pkg_info.platform['config_filepath']
        self.config  = Configuration(config_filepath)
        
    def _load_all_devices(self):
        for name in self.config['devices'].keys():
            print "Loading device '%s'..." % name,
            try:
                device = self.config.load_device(name)
                print "success."
            except Exception, exc:
                print "failed loading device '%s' with exception: %s" % (name, exc)

    def _load_all_controllers(self):
        try:
            controllers_dict = self.config['controllers']
            for name in controllers_dict.keys():
                print "Loading controller '%s'..." % name,
                try:
                    controller = self.config.load_controller(name)
                    print "success."
                except Exception, exc:
                    print "failed loading controller '%s' with exception: %s" % (name, exc)
        except KeyError:
            pass


    def start_shell(self, msg = ""):
        status_msg = []
        status_msg.append(msg)
        
        #load convenient modules
        self.user_ns['time'] = time
        
        #find the available devices
        items = self.config._device_cache.items()
        items.sort()
        status_msg.append("Available devices:")
        for name, device in items:
            status_msg.append("\t%s" % name)
            #add device name to the user name space
            self.user_ns[name] = device
        
        #find the available controllers
        items = self.config._controller_cache.items()
        items.sort()
        status_msg.append("Available controllers:")
        for name, controller in items:
            status_msg.append("\t%s" % name)
            #add controller name to the user name space
            self.user_ns[name] = controller  
        
        #add all the special commands to the namespace
        self.user_ns.update(self.commands) 

        #complete the status message
        status_msg.append('')
        status_msg.append("-- Hit Ctrl-D to exit. --")
        status_msg = '\n'.join(status_msg) 
        #start the shell
        ipshell = None
        try:
            ipshell = IPYTHON_SHELL(user_ns = self.user_ns, banner1 = status_msg) #FIXME change made for ipython >= 0.13
            ipshell.mainloop() #FIXME change made for ipython >= 0.13
        except TypeError: #FIXME support older versions
            ipshell = IPYTHON_SHELL(user_ns = self.user_ns)
            ipshell.mainloop(banner = status_msg)
            

__commands = {}

###############################################################################
# Main
def main():
    app = Application(commands=__commands)
    app.load()
    app.start_shell(msg = __BANNER)

