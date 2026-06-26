@echo off
setlocal
cd /d "%~dp0"
if not exist .venv (
  py -3.11 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python tools\create_windows_icon.py
pyinstaller --noconfirm --clean --windowed ^
  --name TcpRecorderProxy ^
  --paths "src" ^
  --icon "build\app_icon.ico" ^
  --add-data "config;config" ^
  --add-data "src\recorder_proxy\gui\assets;recorder_proxy\gui\assets" ^
  --hidden-import recorder_proxy.app.bootstrap ^
  --hidden-import recorder_proxy.gui.main_window ^
  run.py
echo Build output: dist\TcpRecorderProxy\TcpRecorderProxy.exe
endlocal
