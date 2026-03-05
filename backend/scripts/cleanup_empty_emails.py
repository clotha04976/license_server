"""
清理腳本：將 customers 表中空字串的 email 轉換為 NULL

這個腳本會將所有 email 欄位為空字串的記錄轉換為 NULL，
以避免唯一性約束錯誤。

執行方式：
    python scripts/cleanup_empty_emails.py
"""
import logging
import sys
import os

# Add the project root to the Python path to allow for correct module imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from sqlalchemy import text
from app.db.session import SessionLocal
from app.models.customer import Customer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_empty_emails():
    """
    將所有空字串的 email 轉換為 NULL
    """
    db = SessionLocal()
    try:
        # 查詢所有 email 為空字串的記錄
        customers_with_empty_email = db.query(Customer).filter(
            Customer.email == ''
        ).all()
        
        count = len(customers_with_empty_email)
        
        if count == 0:
            logger.info("沒有找到 email 為空字串的記錄，無需清理。")
            return
        
        logger.info(f"找到 {count} 筆 email 為空字串的記錄，開始清理...")
        
        # 將空字串轉換為 None (NULL)
        for customer in customers_with_empty_email:
            customer.email = None
            logger.info(f"客戶 ID {customer.id} ({customer.name}) 的 email 已轉換為 NULL")
        
        db.commit()
        logger.info(f"成功清理 {count} 筆記錄。")
        
    except Exception as e:
        logger.error(f"清理過程中發生錯誤: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("開始清理空字串 email...")
    cleanup_empty_emails()
    logger.info("清理完成。")

