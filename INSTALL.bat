@echo off
rem sakuna-translation-patch - deutschen Patch bauen und installieren (Doppelklick)
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 install.py %*
) else (
    python install.py %*
)
echo.
pause
