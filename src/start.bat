@echo off

:: this script is used to start the main program so
:: that the user does not need to run it through the CLI

cd "%~dp0"
if exist "csgo-autobenchmark.py" (
    "csgo-autobenchmark.py"
) else (
    if exist "csgo-autobenchmark.exe" (
        "csgo-autobenchmark.exe"
    )
)

pause
exit /b
