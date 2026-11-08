@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" "scripts\send_whatsapp_reminders.py"
) else (
  python "scripts\send_whatsapp_reminders.py"
)
exit /b %errorlevel%
