################################################################################
from automat.services.application import ShellApplication

import OLMpstat.pkg_info
################################################################################
__BANNER  = ['*'*80,
             '* OLMpstat Shell',
             '*     author: cversek@pvos.org',
             '*'*80]
__BANNER  = '\n'.join(__BANNER)

class Application(ShellApplication):
    pass #FIXME can overload generic behaviors here

###############################################################################
# Main
def main():
    config_filepath = OLMpstat.pkg_info.platform['config_filepath']
    app = Application()
    app.load(config_filepath = config_filepath)
    app.start_shell(msg = __BANNER)

