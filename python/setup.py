#!/usr/bin/python
"""   
desc:  Setup script for 'OLMpstat' package.
auth:  Craig Wm. Versek (craig@pvos.org)
date:  2013-09-02
notes: Install with "python setup.py install".
"""
import platform, os, shutil

PACKAGE_METADATA = {
    'name'         : 'OLMpstat',
    'version'      : 'dev',
    'author'       : "Craig Wm. Versek",
    'author_email' : "craig@pvos.org",
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
                                      'olm_pstat_control = OLMpstat.scripts.control:main',
                                     ],
                  'console_scripts': [
                                      'olm_pstat_shell  = OLMpstat.scripts.shell:main',
                                      'olm_pstat_status = OLMpstat.scripts.status:main',
                                     ],
                }
 
if __name__ == "__main__":
    from setuptools import setup, find_packages    
    setup(package_dir      = {'':PACKAGE_SOURCE_DIR},
          packages         = find_packages(PACKAGE_SOURCE_DIR),
          entry_points     = ENTRY_POINTS,
          #non-code files
          #package_data     =   {'': ['*.so']},

          **PACKAGE_METADATA
         )
     

