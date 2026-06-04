@echo off
title JiangXiaoChuang

echo.
echo   JiangXiaoChuang - Wuhan Cultural AI Designer
echo   =============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Python not found. Please install Python 3.10+
    echo   https://www.python.org/downloads/
    pause
    exit /b 1
)

echo   [OK] Python ready

echo   [..] Installing dependencies...
pip install -r requirements.txt -q 2>nul

echo   [OK] Dependencies ready

if not exist ".env" (
    echo   [!!] .env file not found, creating from template
    echo   Please edit .env and add your Bailian API Key
    echo   https://bailian.console.aliyun.com
    copy .env.example .env >nul 2>&1
)

echo.
echo   Starting...
echo   Open http://localhost:8501 in your browser
echo   Press Ctrl+C to stop
echo.

start "" http://localhost:8501
streamlit run app.py --server.port 8501
pause
