@echo off
rem One-click build: self-contained Windows executables for eBIRForms2PDF.
rem Produces dist\eBIRForms2PDF.exe (desktop app) and dist\ebirforms2pdf-cli.exe.
rem Rendering still needs Microsoft Edge or Google Chrome installed on the machine.
setlocal
cd /d "%~dp0"
.\.venv\Scripts\python.exe -m pip install -e . pyinstaller || exit /b 1
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name eBIRForms2PDF --collect-all playwright launch_gui.py || exit /b 1
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --name ebirforms2pdf-cli --collect-all playwright launch_cli.py || exit /b 1
echo.
echo Built executables:
dir /b dist\*.exe
endlocal
