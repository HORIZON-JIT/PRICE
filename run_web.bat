@echo off
chcp 65001 >nul
call .venv\Scripts\activate.bat
streamlit run src/price/app.py
