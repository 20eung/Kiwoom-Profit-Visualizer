@echo off
REM Windows Batch File for Kiwoom Profit Visualizer
REM 실행 종료 (스케줄러용 pause 제거)line daily

cd /d %~dp0

if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe run_pipeline.py --credentials credentials.json
) else (
    echo [ERROR] Virtual environment venv not found.
    python run_pipeline.py --credentials credentials.json
)

pause
