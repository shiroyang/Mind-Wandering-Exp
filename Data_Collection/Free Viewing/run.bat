@echo off
setlocal

:: Start TobiiRecorder.py in a separate window
start "TobiiRecorder" python TobiiRecorder.py

:: Wait for 1 seconds before starting test_lastrun.py
timeout /t 1 >nul

:: Start test_lastrun.py and capture its PID
start /min "Experiment" cmd /c python free_viewing_lastrun.py
for /f "tokens=2" %%i in ('tasklist /v ^| findstr /i "Experiment"') do set PID=%%i

:: Continuously check if test_lastrun.py has completed
:loop
tasklist /fi "PID eq %PID%" | findstr "%PID%"
if errorlevel 1 (
    :: test_lastrun.py has finished, now terminate TobiiRecorder.py
    for /f "tokens=2" %%i in ('tasklist /v ^| findstr /i "TobiiRecorder"') do (
        taskkill /PID %%i /F
    )
    goto :end
) else (
    :: Wait for a bit before checking again
    timeout /t 2 >nul
    goto loop
)

:end
endlocal
