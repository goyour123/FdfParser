import os, sys
from cx_Freeze import setup, Executable

os.environ['TCL_LIBRARY'] = sys.exec_prefix + r'\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = sys.exec_prefix + r'\tcl\tk8.6'

base = 'None'
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'include_files': [sys.exec_prefix + r'\DLLs\tk86t.dll', sys.exec_prefix + r'\DLLs\tcl86t.dll', '.\img']
    }
}

executables = [
    Executable(script='FdVisualizer.py', base=base, icon='.\img\\trilobite.ico')
]

setup(name='FdVisualizer',
      version='3.2',
      description='Visualize fdf layout',
      executables=executables,
      options=options
      )
