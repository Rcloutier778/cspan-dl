@echo off
python main.py
if %errorlevel% == 0 goto end
set /p="Exited with non-0 status. Press any key to continue."

:end
