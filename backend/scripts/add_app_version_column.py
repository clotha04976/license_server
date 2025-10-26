#!/usr/bin/env python3
"""
新增 app_version 欄位到 activations 表格的腳本
"""

import sqlite3
import os
import sys

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def add_app_version_column():
    """新增 app_version 欄位到 activations 表格"""
    try:
        # 連接到資料庫
        conn = sqlite3.connect(settings.DATABASE_URL.replace("sqlite:///", ""))
        cursor = conn.cursor()
        
        # 檢查欄位是否已存在
        cursor.execute("PRAGMA table_info(activations)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'app_version' in columns:
            print("app_version 欄位已存在，跳過新增。")
            return
        
        # 新增 app_version 欄位
        cursor.execute("ALTER TABLE activations ADD COLUMN app_version VARCHAR(50)")
        conn.commit()
        
        print("成功新增 app_version 欄位到 activations 表格。")
        
    except Exception as e:
        print(f"新增欄位時發生錯誤: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
    
    return True

if __name__ == "__main__":
    add_app_version_column()

