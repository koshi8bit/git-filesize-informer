@echo off
setlocal
set "FULL_PATH=%~dp0venv\Scripts\python.exe"
%FULL_PATH% %~dp0main.py %*
endlocal