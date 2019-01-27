@setlocal EnableDelayedExpansion

@set PYTHON3_PATH="C:\Program Files (x86)\Python36-32\python.exe"

@if not exist %PYTHON3_PATH% (
    @echo %PYTHON3_PATH% Not Found!
    goto AUTO
) else (
    @echo Found python.exe %PYTHON3_PATH%
    goto BUILDEXE
)

:AUTO
@for /f "delims=" %%a in ('where python.exe') do @set PYTHON3_PATH="%%a"
@if not exist %PYTHON3_PATH% (
    @echo Auto searching python.exe not found. Please add python.exe to PATH variable.
    goto END
) else (
    @echo Found python.exe %PYTHON3_PATH%
    goto BUILDEXE
)

:BUILDEXE
@rmdir %cd%\build /s /q
%PYTHON3_PATH% .\setup_cxfreeze.py build

:END
@pause
