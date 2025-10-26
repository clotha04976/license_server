@echo off
echo 執行資料庫遷移：新增 app_version 欄位
cd /d "%~dp0"
python scripts/add_app_version_column.py
pause

