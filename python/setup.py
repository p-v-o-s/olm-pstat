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
 
if __name__ == "__main__":
    from setuptools import setup, find_packages    
    setup(package_dir      = {'':PACKAGE_SOURCE_DIR},
          packages         = find_packages(PACKAGE_SOURCE_DIR),
          
          #non-code files
          #package_data     =   {'': ['*.so']},

          **PACKAGE_METADATA
         )
     

