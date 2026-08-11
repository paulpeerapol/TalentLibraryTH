@echo off
:: ========================================================
:: eBook to e-Learning Studio - One-Click Launcher
:: ========================================================
title eBook to e-Learning Studio
echo Starting eBook to e-Learning Studio Web App...
cd /d "%~dp0"

:: Check Python and launch Streamlit Web App automatically in browser
python -m streamlit run app.py --server.headless=false

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while starting the Web App.
    pause
)
