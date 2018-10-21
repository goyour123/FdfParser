@set PYTHON3_PATH="C:\Program Files (x86)\Python36-32\python.exe"
@rmdir %cd%\build /s /q
%PYTHON3_PATH% .\setup_cxfreeze.py build
@pause