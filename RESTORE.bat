@echo off
rem sakuna-translation-patch - auf die Originaldateien zuruecksetzen (Doppelklick)
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 install.py --restore %*
) else (
    python install.py --restore %*
)
echo.
pause
