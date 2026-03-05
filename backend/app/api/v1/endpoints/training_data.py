from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Body
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
import os
import shutil
import json
import csv
from pathlib import Path
import logging
from zoneinfo import ZoneInfo
import pandas as pd

logger = logging.getLogger(__name__)

from .... import models, schemas
from ....core.dependencies import get_db
from ....core import security

# Public router (只有上傳端點)
public_router = APIRouter()

# Internal router (所有端點，包含查詢)
internal_router = APIRouter()

# 訓練資料儲存根目錄
_is_docker = os.path.exists("/app/app")
_default_dataset_dir = "/app/dataset_to_train" if _is_docker else str(Path(__file__).parent.parent.parent.parent.parent / "dataset_to_train")
DATASET_BASE_DIR = Path(os.getenv("DATASET_DIR", _default_dataset_dir))

# 確保目錄存在
DATASET_BASE_DIR.mkdir(parents=True, exist_ok=True)
logger.info(f"訓練資料儲存目錄: {DATASET_BASE_DIR} (絕對路徑: {DATASET_BASE_DIR.resolve()})")

# 台北時區
TAIPEI_TZ = ZoneInfo("Asia/Taipei")

def to_taipei_time(dt: datetime) -> datetime:
    """將 datetime 轉換為台北時區"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(TAIPEI_TZ)

def get_dataset_dir(year: int, month: int, serial_number: str) -> Path:
    """取得指定年月和序號的訓練資料目錄"""
    period_dir = DATASET_BASE_DIR / f"{year}.{str(month).zfill(2)}"
    dataset_dir = period_dir / serial_number
    dataset_dir.mkdir(parents=True, exist_ok=True)
    return dataset_dir

def convert_tax_type(tax_type: str) -> str:
    """轉換課稅別格式（支援 "應稅"/"零稅"/"免稅" 和 "1"/"2"/"3"）"""
    if tax_type == "應稅":
        return "1"
    elif tax_type == "零稅":
        return "2"
    elif tax_type == "免稅":
        return "3"
    # 如果已經是數字格式，直接返回
    if tax_type in ["1", "2", "3"]:
        return tax_type
    # 預設為應稅
    return "1"

def format_date(date_string: str) -> str:
    """格式化日期（民國年轉西元年）"""
    if date_string and len(date_string) == 7:
        roc_year = date_string[0:3]
        west_year = int(roc_year) + 1911
        return f"{west_year}/{date_string[3:5]}/{date_string[5:7]}"
    return date_string

def get_filename_key(path_str: str) -> str:
    """提取路徑中的檔名並轉小寫作為比對鍵"""
    if not path_str:
        return ""
    return os.path.basename(str(path_str)).lower()

@public_router.post("/upload", response_model=schemas.TrainingDataUploadResponse)
async def upload_training_data(
    serial_number: str = Form(...),
    year: int = Form(...),
    month: int = Form(...),
    invoices_data: str = Form(...),  # JSON 字串
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    上傳訓練資料
    - 驗證序號是否存在於資料庫
    - 建立目錄結構：dataset_to_train/{year.month}/{serial_number}/
    - 儲存圖片檔案
    - 處理 CSV 合併邏輯（同年度月份新增，重複發票覆蓋）
    """
    # 驗證序號是否存在
    license_obj = db.query(models.License).options(
        joinedload(models.License.customer)
    ).filter(models.License.serial_number == serial_number).first()
    
    if not license_obj:
        raise HTTPException(
            status_code=403,
            detail=f"序號 '{serial_number}' 不存在於資料庫中，拒絕上傳。"
        )
    
    # 解析發票資料 JSON
    try:
        invoices_list = json.loads(invoices_data)
        invoices = [schemas.InvoiceData(**inv) for inv in invoices_list]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"發票資料格式錯誤: {str(e)}")
    
    # 取得儲存目錄
    dataset_dir = get_dataset_dir(year, month, serial_number)
    csv_path = dataset_dir / "data.csv"
    metadata_path = dataset_dir / "metadata.json"
    
    # 讀取或建立 metadata
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        uploaded_at = datetime.fromisoformat(metadata.get('uploaded_at', datetime.now(TAIPEI_TZ).isoformat()))
    else:
        uploaded_at = datetime.now(TAIPEI_TZ)
        metadata = {
            "serial_number": serial_number,
            "year": year,
            "month": month,
            "uploaded_at": uploaded_at.isoformat(),
            "invoice_count": 0,
            "last_updated": uploaded_at.isoformat()
        }
    
    # 建立圖片檔名對應表（從上傳的檔案）
    # image_map: 上傳檔案的原始檔名 -> 實際儲存檔名
    image_map = {}
    uploaded_images = 0
    failed_images = 0
    
    # 處理上傳的圖片檔案
    for image_file in images:
        try:
            # 使用原始檔名儲存（已經由客戶端處理過路徑）
            safe_filename = image_file.filename.replace('\\', '_').replace('/', '_')
            image_path = dataset_dir / safe_filename
            
            # 儲存圖片
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image_file.file, buffer)
            
            # 建立對應關係：原始檔名 -> 實際儲存檔名
            # image_file.filename 是從客戶端傳來的檔名（應該是原始檔名）
            image_map[image_file.filename] = safe_filename
            
            uploaded_images += 1
            logger.info(f"成功儲存圖片: {image_path}")
        except Exception as e:
            failed_images += 1
            logger.error(f"儲存圖片失敗 {image_file.filename}: {e}")
    
    csv_updated = False
    
    # 讀取現有 CSV 資料（如果存在）
    existing_data = {}
    existing_rows = []
    if csv_path.exists():
        try:
            with open(csv_path, mode="r", encoding="big5", errors="ignore", newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    invoice_number = row.get("發票號碼", "")
                    if invoice_number:
                        existing_data[invoice_number] = row
                        existing_rows.append(row)
        except Exception as e:
            logger.warning(f"讀取現有 CSV 失敗: {e}")
    
    # 處理每筆發票資料
    for invoice in invoices:
        # 準備 CSV 資料
        invoice_type = invoice.invoice_type[:2] if invoice.invoice_type else ""
        deductible = 1 if invoice.deductible or invoice_type.startswith('3') else 2
        
        # 取得圖片檔名
        # 從發票的 img_path 取得原始檔名
        original_img_filename = os.path.basename(invoice.img_path) if invoice.img_path else ""
        
        # 在 image_map 中查找對應的實際儲存檔名
        # 嘗試多種可能的 key 格式
        img_filename = original_img_filename
        if original_img_filename:
            # 先嘗試原始檔名
            if original_img_filename in image_map:
                img_filename = image_map[original_img_filename]
            # 再嘗試小寫檔名
            elif original_img_filename.lower() in image_map:
                img_filename = image_map[original_img_filename.lower()]
            # 如果都找不到，使用原始檔名（可能圖片已經存在或上傳失敗）
            else:
                img_filename = original_img_filename
        
        csv_row = {
            "發票號碼": invoice.invoice_number,
            "發票類別": invoice_type,
            "發票日期": format_date(invoice.invoice_date),
            "承賣人統編": invoice.seller_id or "",
            "買受人統編": invoice.buyer_id or "",
            "憑證類別": "",
            "課稅別": convert_tax_type(invoice.tax_type),
            "類別": 2 if invoice.is_fix_asset else 1,
            "金額": invoice.sales_amount or 0,
            "稅額": invoice.business_tax or 0,
            "是否折抵": deductible,
            "圖片檔": img_filename,  # 使用實際儲存的檔名
            "傳票編號": "",
            "異常欄": "",
            "是否已轉入巨將": existing_data.get(invoice.invoice_number, {}).get("是否已轉入巨將", ""),
            "第幾次掃描": 1,
            "起始年月": "",
            "結束年月": "",
            "已異動": "",
        }
        
        # 如果發票已存在，覆蓋；否則新增
        if invoice.invoice_number in existing_data:
            # 覆蓋現有資料
            for i, row in enumerate(existing_rows):
                if row.get("發票號碼") == invoice.invoice_number:
                    existing_rows[i] = csv_row
                    break
        else:
            # 新增資料
            existing_rows.append(csv_row)
    
    # 寫回 CSV 檔案
    if existing_rows:
        try:
            df = pd.DataFrame(existing_rows)
            with open(csv_path, "w", newline="", encoding="big5", errors="ignore") as csvfile:
                df.to_csv(csvfile, index=False, quoting=csv.QUOTE_NONE)
            csv_updated = True
        except PermissionError:
            raise HTTPException(
                status_code=403,
                detail="CSV檔案目前被其他程式開啟中，請先關閉檔案後再試。"
            )
        except OSError as e:
            if "Permission denied" in str(e) or "存取被拒" in str(e):
                raise HTTPException(
                    status_code=403,
                    detail="CSV檔案目前被其他程式開啟中，請先關閉檔案後再試。"
                )
            raise
    
    # 更新 metadata
    last_updated = datetime.now(TAIPEI_TZ)
    metadata["last_updated"] = last_updated.isoformat()
    metadata["invoice_count"] = len(existing_rows)
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return schemas.TrainingDataUploadResponse(
        status="success",
        message=f"成功處理 {len(invoices)} 筆發票資料，上傳 {uploaded_images} 張圖片",
        uploaded_images=uploaded_images,
        failed_images=failed_images,
        csv_updated=csv_updated
    )

@internal_router.get("/", response_model=schemas.TrainingDataListResponse, dependencies=[Depends(security.get_current_active_admin)])
def list_training_data(
    serial_number: Optional[str] = Query(None, description="依序號篩選"),
    customer_id: Optional[int] = Query(None, description="依客戶 ID 篩選"),
    page: int = Query(1, ge=1, description="頁碼"),
    limit: int = Query(20, ge=1, le=10000, description="每頁筆數"),
    db: Session = Depends(get_db),
):
    """
    列出所有訓練資料上傳記錄（管理員專用）
    """
    all_records = []
    
    if not DATASET_BASE_DIR.exists():
        return schemas.TrainingDataListResponse(
            items=[],
            total=0,
            page=1,
            limit=limit,
            total_pages=0
        )
    
    # 掃描所有年月目錄
    for period_dir in DATASET_BASE_DIR.iterdir():
        if not period_dir.is_dir():
            continue
        
        # 解析年月（格式：114.08）
        try:
            period_parts = period_dir.name.split('.')
            if len(period_parts) == 2:
                year = int(period_parts[0])
                month = int(period_parts[1])
            else:
                continue
        except:
            continue
        
        # 掃描該年月下的所有序號目錄
        for serial_dir in period_dir.iterdir():
            if not serial_dir.is_dir():
                continue
            
            serial_num = serial_dir.name
            
            # 如果指定了序號篩選，跳過不符合的
            if serial_number and serial_num != serial_number:
                continue
            
            # 讀取 metadata.json
            metadata_path = serial_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                uploaded_at = datetime.fromisoformat(metadata.get('uploaded_at', datetime.now(TAIPEI_TZ).isoformat()))
                last_updated = datetime.fromisoformat(metadata.get('last_updated', uploaded_at.isoformat()))
                invoice_count = metadata.get('invoice_count', 0)
                
                all_records.append({
                    "serial_number": serial_num,
                    "year": year,
                    "month": month,
                    "uploaded_at": uploaded_at,
                    "last_updated": last_updated,
                    "invoice_count": invoice_count,
                })
            except Exception as e:
                logger.warning(f"讀取 metadata 失敗 {metadata_path}: {e}")
                continue
    
    # 依客戶 ID 篩選
    if customer_id:
        licenses = db.query(models.License).filter(
            models.License.customer_id == customer_id
        ).all()
        serial_numbers = {license.serial_number for license in licenses}
        all_records = [r for r in all_records if r["serial_number"] in serial_numbers]
    
    # 取得客戶資訊
    record_items = []
    for record in all_records:
        license_obj = db.query(models.License).options(
            joinedload(models.License.customer)
        ).filter(models.License.serial_number == record["serial_number"]).first()
        
        record_items.append(schemas.TrainingDataRecord(
            serial_number=record["serial_number"],
            year=record["year"],
            month=record["month"],
            uploaded_at=record["uploaded_at"],
            last_updated=record["last_updated"],
            invoice_count=record["invoice_count"],
            customer_id=license_obj.customer.id if license_obj else None,
            customer_name=license_obj.customer.name if license_obj else None,
            customer_tax_id=license_obj.customer.tax_id if license_obj else None,
        ))
    
    # 排序（最新的在前）
    record_items.sort(key=lambda x: x.last_updated, reverse=True)
    
    # 分頁
    total = len(record_items)
    total_pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    end = start + limit
    paginated_items = record_items[start:end]
    
    return schemas.TrainingDataListResponse(
        items=paginated_items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )
