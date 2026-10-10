@echo off
rem One-click build: self-contained Windows executables for eBIRForms2PDF.
rem Produces dist\eBIRForms2PDF.exe (desktop app) and dist\ebirforms2pdf-cli.exe.
rem Rendering still needs Microsoft Edge or Google Chrome installed on the machine.
rem Keep the package list below in sync with the dependencies in pyproject.toml.
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo ERROR: %PY% not found. Create it first, from this folder:
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install .
    goto :fail
)
"%PY%" -m pip install pefile playwright pypdf pyinstaller || goto :fail
"%PY%" -m PyInstaller --noconfirm --clean --onefile --windowed --name eBIRForms2PDF --collect-all playwright launch_gui.py || goto :fail
"%PY%" -m PyInstaller --noconfirm --clean --onefile --name ebirforms2pdf-cli --collect-all playwright launch_cli.py || goto :fail
echo.
echo Built executables:
dir /b dist\*.exe
endlocal
if "%~1"=="" pause
exit /b 0

:fail
echo.
echo Build FAILED. See the messages above.
endlocal
if "%~1"=="" pause
exit /b 1
