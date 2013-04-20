# Run as "python setup.py py2exe"
from distutils.core import setup
import py2exe

setup(windows=[{"script": "ui.pyw"}],
      name="Structured Editor",
      #data_files = [("", ["interface.ui", "janela_gramatica.ui"])],
      options={"py2exe": {"includes":
                          ["sip",
                           "dbhash"],
                          "dll_excludes": ["MSVCP90.dll", "w9xpopen.exe"],
                          "optimize": 2,
                          "bundle_files": 1,
                          "compressed": True,
                         }},
     zipfile = None,
     )
