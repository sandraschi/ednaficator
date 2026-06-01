@echo off
echo Killing ports 10942 and 10943...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":10942"') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| find ":10943"') do taskkill /f /pid %%a 2>nul

echo Wiping Vite cache...
rd /s /q "D:\Dev\repos\ednaficator\ui\node_modules\.vite" 2>nul

echo Reinstalling frontend deps...
cd /d "D:\Dev\repos\ednaficator\ui"
call npm install

echo Done. Now run ednaficator-start.bat
pause
