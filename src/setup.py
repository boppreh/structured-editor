# Run as "python setup.py py2exe"
from distutils.core import setup
from sys import argv
import py2exe

if __name__ == '__main__' and len(argv) < 2:
    argv.append('py2exe')

setup(windows=[{"script": "main.pyw",
                "icon_resources": [(1, "editor.ico")],
                "dest_base": "Editor",
               }],
      name="Structured Editor",
      options={"py2exe": {"includes": ["sip",
                                       "PyQt4.QtNetwork",
                                       "dbhash"],
                          "dll_excludes": ["MSVCP90.dll", "w9xpopen.exe"],
                          "optimize": 2,
                          "bundle_files": 1,
                          "compressed": True,
                         }},
     zipfile = None,
     )

import shutil, os
if os.path.exists('../dist/Editor.exe'):
    os.remove('../dist/Editor.exe')
os.rename('dist/Editor.exe', '../dist/Editor.exe')
shutil.rmtree('dist', ignore_errors=True)
shutil.rmtree('build', ignore_errors=True)
