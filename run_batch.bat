@echo off
chcp 65001 >nul
call .venv\Scripts\activate.bat

if "%~1"=="" (
    echo 使い方: run_batch.bat 入力ファイル.xlsx 出力ファイル.xlsx
    echo 例:     run_batch.bat parts.xlsx result.xlsx
    pause
    exit /b 1
)

if "%~2"=="" (
    echo 使い方: run_batch.bat 入力ファイル.xlsx 出力ファイル.xlsx
    pause
    exit /b 1
)

python -m price.main -i "%~1" -o "%~2" %3 %4 %5 %6
pause
