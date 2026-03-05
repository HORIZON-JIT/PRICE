@echo off
chcp 65001 >nul
echo ============================================================
echo   価格演算システム セットアップ
echo ============================================================
echo.

REM Python確認
python --version >nul 2>&1
if errorlevel 1 (
    echo [エラー] Pythonが見つかりません。
    echo Python 3.10以上をインストールしてください。
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 仮想環境を作成中...
if not exist ".venv" (
    python -m venv .venv
)

echo [2/3] パッケージをインストール中...
call .venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -e .

echo [3/3] 設定ファイルを確認中...
if not exist "config\settings.yaml" (
    echo.
    echo [注意] config\settings.yaml が見つかりません。
    echo   config\settings.yaml.example をコピーして
    echo   settings.yaml にリネームし、DB接続情報を記入してください。
    copy config\settings.yaml.example config\settings.yaml >nul
    echo   テンプレートを config\settings.yaml にコピーしました。
)

echo.
echo ============================================================
echo   セットアップ完了
echo ============================================================
echo.
echo 使い方:
echo   Web UI:    run_web.bat をダブルクリック
echo   バッチ:    run_batch.bat 入力.xlsx 出力.xlsx
echo.
pause
