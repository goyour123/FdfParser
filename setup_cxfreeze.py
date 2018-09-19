import os, sys
from cx_Freeze import setup, Executable

python3_path = r'C:\Users\Ren.Yang\AppData\Local\Programs\Python\Python36-32'

os.environ['TCL_LIBRARY'] = python3_path + r'\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = python3_path + r'\tcl\tk8.6'

base = 'None'
if sys.platform == 'win32':
    base = 'Win32GUI'

options = {
    'build_exe': {
        'include_files': [python3_path + r'\DLLs\tk86t.dll', python3_path + r'\DLLs\tcl86t.dll']
    }
}

executables = [
    Executable('FdVisualizer.py', base=base)
]

setup(name='FdVisualizer',
      version='1.0',
      description='Visualize fdf layout',
	  executables=executables,
	  options=options
	  )
