#!/usr/bin/python
"""   
desc:  Setup script for 'OLMpstat' package.
auth:  Craig Wm. Versek (cversek@pvos.org)
date:  2013-09-02
notes: Install with "python setup.py install".
"""
import platform, os, shutil

PACKAGE_METADATA = {
    'name'         : 'OLMpstat',
    'version'      : 'dev',
    'author'       : "Craig Wm. Versek",
    'author_email' : "cversek@pvos.org",
}
    
PACKAGE_SOURCE_DIR = 'src'
MAIN_PACKAGE_DIR   = 'OLMpstat'
MAIN_PACKAGE_PATH  = os.path.abspath(os.sep.join((PACKAGE_SOURCE_DIR,MAIN_PACKAGE_DIR)))

#dependencies
INSTALL_REQUIRES = [
                    'numpy >= 1.1.0',
                    'matplotlib >= 0.98',
                    'pyyaml',
                    'pmw',
                    'pyserial',
                    ]

#scripts and plugins
ENTRY_POINTS =  { 'gui_scripts':     [
                                      'olm_pstat_control = OLMpstat.apps.control.main:main',
                                     ],
                  'console_scripts': [
                                      'olm_pstat_shell  = OLMpstat.scripts.shell:main',
                                      'olm_pstat_status = OLMpstat.scripts.status:main',
                                     ],
                }

DEFAULT_CONFIG_FILENAME          = 'testing.cfg'
EXAMPLE_CONFIG_FILENAME          = 'EXAMPLE.cfg'
LINUX_AUTOMAT_CONFIG_DIR         = '/etc/Automat'
LINUX_OLM_PSTAT_CONFIG_DIR       = '/etc/Automat/olm_pstat'

 
def setup_platform_config():
    print "\nSetting up the configuration file:"
    
    #gather platform specific data
    platform_data = {}   
    system = platform.system()
    config_filedir               = None
    default_config_filepath      = None
    example_calibration_filepath = None 
    print "detected system: %s" % system
    if system == 'Linux' or system == 'Darwin':
        if not os.path.isdir(LINUX_AUTOMAT_CONFIG_DIR):
            os.mkdir(LINUX_AUTOMAT_CONFIG_DIR)
        config_filedir = LINUX_OLM_PSTAT_CONFIG_DIR
        if not os.path.isdir(config_filedir):
            os.mkdir(config_filedir)
        default_config_filepath = os.sep.join((config_filedir, DEFAULT_CONFIG_FILENAME))
    elif system == 'Windows':
        from win32com.shell import shellcon, shell
        appdata_path =  shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
        default_config_filepath = os.sep.join((appdata_path, DEFAULT_CONFIG_FILENAME))

    #if the configuration file does NOT exist, than copy the example file to that location
    if not os.path.isfile(default_config_filepath):
        print "copying the example config file to '%s', please change these settings to match your system" % default_config_filepath
        shutil.copy(EXAMPLE_CONFIG_FILENAME,default_config_filepath)
    else:
        print "settings file already exists at '%s'; not overwriting; check the documention to see if additional settings are required" % default_config_filepath
    raw_input("press 'Enter' to continue...")

    #autogenerate the package information file
    platform_data['system']          = system
    platform_data['config_filedir']  = config_filedir
    platform_data['config_filepath'] = default_config_filepath
    pkg_info_filename   = os.sep.join((MAIN_PACKAGE_PATH,'pkg_info.py'))
    pkg_info_file       = open(pkg_info_filename,'w')
    pkg_info_file.write("metadata = %r\n" % PACKAGE_METADATA)
    pkg_info_file.write("platform = %r"   % platform_data)
    pkg_info_file.close()

if __name__ == "__main__":
    from setuptools import setup, find_packages
    #run the platform specific configuration
    setup_platform_config()
    #complete the setup using setuptools
    setup(package_dir      = {'':PACKAGE_SOURCE_DIR},
          packages         = find_packages(PACKAGE_SOURCE_DIR),
          entry_points     = ENTRY_POINTS,
          #non-code files
          #package_data     =   {'': ['*.so']},
          **PACKAGE_METADATA
         )

