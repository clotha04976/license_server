from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
import os
import shutil
from pathlib import Path
import logging
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

from .... import models, schemas
from ....core.dependencies import get_db
from ....core import security

# Public router (只有上傳端點)
public_router = APIRouter()

# Internal router (所有端點，包含查詢)
internal_router = APIRouter()

# Log 檔案儲存根目錄
# 優先使用環境變數，否則使用預設路徑
# 在 Docker 容器中，應該使用 /app/logs（對應到主機的 ./backend/logs）
# 在本地開發時，使用相對路徑 backend/logs
_default_logs_dir = "/app/logs" if os.path.exists("/app") else str(Path(__file__).parent.parent.parent.parent.parent / "logs")
LOGS_BASE_DIR = Path(os.getenv("LOGS_DIR", _default_logs_dir))
logger.info(f"Log 檔案儲存目錄: {LOGS_BASE_DIR}")

# 台北時區
TAIPEI_TZ = ZoneInfo("Asia/Taipei")

def get_log_dir(serial_number: str) -> Path:
    """取得指定序號的 log 目錄"""
    log_dir = LOGS_BASE_DIR / serial_number
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def to_taipei_time(dt: datetime) -> datetime:
    """將 datetime 轉換為台北時區"""
    if dt.tzinfo is None:
        # 如果沒有時區資訊，假設是 UTC
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(TAIPEI_TZ)

@public_router.post("/upload", response_model=schemas.LogUploadResponse)
async def upload_logs(
    serial_number: str = Form(...),
    files: List[UploadFile] = File(...),
    problem_description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    上傳 log 檔案
    - 驗證序號是否存在於資料庫
    - 只允許 .log 檔案
    - 儲存到 backend/logs/{serial_number}/ 目錄
    - 同一時間上傳的檔案使用相同的批次 ID
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
    
    # 生成批次 ID（同一時間上傳的檔案共用同一個批次 ID）
    # 使用台北時區
    batch_id = datetime.now(TAIPEI_TZ).strftime("%Y%m%d_%H%M%S")
    
    uploaded_files = []
    failed_files = []
    
    for file in files:
        # 驗證檔案類型
        # 支援標準 .log 檔案和帶日期後綴的 .log.YYYY-MM-DD 檔案
        filename_lower = file.filename.lower()
        is_log_file = (
            filename_lower.endswith('.log') or
            ('.log.' in filename_lower and len(filename_lower.split('.log.')) == 2)
        )
        
        if not is_log_file:
            failed_files.append(f"{file.filename} (非 .log 檔案)")
            continue
        
        try:
            # 生成檔名：{batch_id}_{original_filename}
            # 同一批次的所有檔案使用相同的 batch_id
            safe_filename = file.filename.replace('\\', '_').replace('/', '_')
            new_filename = f"{batch_id}_{safe_filename}"
            
            # 取得儲存目錄
            log_dir = get_log_dir(serial_number)
            file_path = log_dir / new_filename
            
            # 儲存檔案
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_files.append(file.filename)
        except Exception as e:
            failed_files.append(f"{file.filename} ({str(e)})")
    
    return schemas.LogUploadResponse(
        status="success" if uploaded_files else "partial" if failed_files else "failed",
        message=f"成功上傳 {len(uploaded_files)} 個檔案，失敗 {len(failed_files)} 個檔案",
        uploaded_files=uploaded_files,
        failed_files=failed_files
    )

@internal_router.get("/", response_model=schemas.LogListResponse, dependencies=[Depends(security.get_current_active_admin)])
def list_logs(
    serial_number: Optional[str] = Query(None, description="依序號篩選"),
    customer_id: Optional[int] = Query(None, description="依客戶 ID 篩選"),
    page: int = Query(1, ge=1, description="頁碼"),
    limit: int = Query(20, ge=1, le=10000, description="每頁筆數"),
    db: Session = Depends(get_db),
):
    """
    列出所有 log 檔案（管理員專用）
    """
    all_logs = []
    
    # 如果指定了序號，只掃描該序號的目錄
    if serial_number:
        log_dir = LOGS_BASE_DIR / serial_number
        if log_dir.exists():
            for file_path in log_dir.glob("*.log"):
                stat = file_path.stat()
                all_logs.append({
                    "file_path": file_path,
                    "filename": file_path.name,
                    "file_size": stat.st_size,
                    "uploaded_at": datetime.fromtimestamp(stat.st_mtime),
                    "serial_number": serial_number
                })
    else:
        # 掃描所有序號目錄
        if LOGS_BASE_DIR.exists():
            for serial_dir in LOGS_BASE_DIR.iterdir():
                if serial_dir.is_dir():
                    for file_path in serial_dir.glob("*.log"):
                        stat = file_path.stat()
                        all_logs.append({
                            "file_path": file_path,
                            "filename": file_path.name,
                            "file_size": stat.st_size,
                            "uploaded_at": datetime.fromtimestamp(stat.st_mtime),
                            "serial_number": serial_dir.name
                        })
    
    # 依客戶 ID 篩選
    if customer_id:
        # 取得該客戶的所有序號
        licenses = db.query(models.License).filter(
            models.License.customer_id == customer_id
        ).all()
        serial_numbers = {license.serial_number for license in licenses}
        all_logs = [log for log in all_logs if log["serial_number"] in serial_numbers]
    
    # 先分組（按批次 ID），然後再分頁
    # 這樣可以確保同一批次的檔案不會被分到不同頁
    batches = {}  # batch_key -> {batch_info, files}
    batch_problem_descriptions = {}  # 批次 ID -> 問題描述
    
    for log in all_logs:
        license_obj = db.query(models.License).options(
            joinedload(models.License.customer)
        ).filter(models.License.serial_number == log["serial_number"]).first()
        
        # 從檔名提取批次 ID（格式：YYYYMMDD_HHMMSS_filename.log）
        batch_id = None
        problem_description = None
        
        # 檔名格式：{batch_id}_{original_filename}
        filename_parts = log["filename"].split('_', 2)
        if len(filename_parts) >= 2:
            # 嘗試解析批次 ID（前兩部分應該是日期和時間）
            try:
                batch_date = filename_parts[0]
                batch_time = filename_parts[1]
                if len(batch_date) == 8 and len(batch_time) == 6:  # YYYYMMDD 和 HHMMSS
                    batch_id = f"{batch_date}_{batch_time}"
            except:
                pass
        
        # 如果無法從檔名提取，使用上傳時間作為批次 ID
        if not batch_id:
            # 轉換為台北時區後再生成批次 ID
            uploaded_at_taipei = to_taipei_time(datetime.fromtimestamp(log["file_path"].stat().st_mtime))
            batch_id = uploaded_at_taipei.strftime("%Y%m%d_%H%M%S")
        
        # 如果是 system_info 檔案，讀取問題描述
        if 'system_info' in log["filename"].lower():
            try:
                with open(log["file_path"], 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '=== 問題描述 ===' in content:
                        # 提取問題描述部分（從 "=== 問題描述 ===" 到下一個 "===" 或檔案結尾）
                        parts = content.split('=== 問題描述 ===')
                        if len(parts) > 1:
                            remaining = parts[1]
                            # 找到下一個 "===" 的位置
                            next_section = remaining.find('===')
                            if next_section > 0:
                                problem_section = remaining[:next_section].strip()
                            else:
                                problem_section = remaining.strip()
                            
                            if problem_section:
                                problem_description = problem_section
                                if batch_id:
                                    batch_problem_descriptions[batch_id] = problem_description
            except Exception as e:
                logger.warning(f"無法讀取 system_info 檔案的問題描述: {e}")
        
        # 使用批次 ID 作為鍵
        batch_key = batch_id
        
        if batch_key not in batches:
            # 轉換上傳時間為台北時區
            uploaded_at_taipei = to_taipei_time(datetime.fromtimestamp(log["file_path"].stat().st_mtime))
            
            batches[batch_key] = {
                "batch_id": batch_id,
                "serial_number": log["serial_number"],
                "customer_id": license_obj.customer.id if license_obj else None,
                "customer_name": license_obj.customer.name if license_obj else None,
                "customer_tax_id": license_obj.customer.tax_id if license_obj else None,
                "uploaded_at": uploaded_at_taipei,
                "problem_description": problem_description,
                "files": []
            }
        
        # 轉換上傳時間為台北時區
        uploaded_at_taipei = to_taipei_time(datetime.fromtimestamp(log["file_path"].stat().st_mtime))
        
        batches[batch_key]["files"].append({
            "filename": log["filename"],
            "file_size": log["file_size"],
            "uploaded_at": uploaded_at_taipei,
            "file_path": log["file_path"],
            "problem_description": problem_description,
        })
    
    # 為同一批次的其他檔案補充問題描述
    for batch_key, batch_data in batches.items():
        if batch_data["batch_id"] in batch_problem_descriptions:
            if not batch_data["problem_description"]:
                batch_data["problem_description"] = batch_problem_descriptions[batch_data["batch_id"]]
            # 也為該批次的所有檔案補充問題描述
            for file_data in batch_data["files"]:
                if not file_data.get("problem_description"):
                    file_data["problem_description"] = batch_problem_descriptions[batch_data["batch_id"]]
    
    # 將批次轉換為陣列並排序（最新的在前）
    batch_list = list(batches.values())
    batch_list.sort(key=lambda x: x["uploaded_at"], reverse=True)
    
    # 分頁（按批次分頁）
    total = len(batch_list)
    total_pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    end = start + limit
    paginated_batches = batch_list[start:end]
    
    # 將所有批次展開為檔案列表（不分頁，讓前端自己分組和分頁）
    log_items = []
    for batch in batch_list:
        for file_data in batch["files"]:
            log_items.append(schemas.LogFileInfo(
                filename=file_data["filename"],
                file_size=file_data["file_size"],
                uploaded_at=file_data["uploaded_at"],
                serial_number=batch["serial_number"],
                customer_id=batch["customer_id"],
                customer_name=batch["customer_name"],
                customer_tax_id=batch["customer_tax_id"],
                batch_id=batch["batch_id"],
                problem_description=batch["problem_description"],
            ))
    
    # 返回所有檔案（不分頁），讓前端自己分組和分頁
    # 這樣可以確保同一批次的檔案不會被分到不同頁
    total = len(log_items)
    total_pages = 1  # 前端會自己計算分頁
    
    return schemas.LogListResponse(
        items=log_items,
        total=total,
        page=1,
        limit=total if total > 0 else 1,
        total_pages=total_pages
    )

@internal_router.get("/download", dependencies=[Depends(security.get_current_active_admin)])
def download_log(
    serial_number: str = Query(..., description="序號"),
    filename: str = Query(..., description="檔案名稱"),
    db: Session = Depends(get_db),
):
    """
    下載指定的 log 檔案（管理員專用）
    """
    # 驗證序號是否存在
    license_obj = db.query(models.License).filter(
        models.License.serial_number == serial_number
    ).first()
    
    if not license_obj:
        raise HTTPException(status_code=404, detail="序號不存在")
    
    # 取得檔案路徑
    log_dir = LOGS_BASE_DIR / serial_number
    file_path = log_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")
    
    # 驗證檔案在正確的目錄中（防止路徑遍歷攻擊）
    if not file_path.resolve().is_relative_to(log_dir.resolve()):
        raise HTTPException(status_code=403, detail="無效的檔案路徑")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="text/plain"
    )

@internal_router.get("/serial/{serial_number}", response_model=List[schemas.LogFileInfo], dependencies=[Depends(security.get_current_active_admin)])
def get_logs_by_serial(
    serial_number: str,
    db: Session = Depends(get_db),
):
    """
    取得指定序號的所有 log 檔案（管理員專用）
    """
    # 驗證序號是否存在
    license_obj = db.query(models.License).options(
        joinedload(models.License.customer)
    ).filter(models.License.serial_number == serial_number).first()
    
    if not license_obj:
        raise HTTPException(status_code=404, detail="序號不存在")
    
    log_dir = LOGS_BASE_DIR / serial_number
    if not log_dir.exists():
        return []
    
    log_items = []
    for file_path in sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = file_path.stat()
        # 轉換為台北時區
        uploaded_at_taipei = to_taipei_time(datetime.fromtimestamp(stat.st_mtime))
        log_items.append(schemas.LogFileInfo(
            filename=file_path.name,
            file_size=stat.st_size,
            uploaded_at=uploaded_at_taipei,
            serial_number=serial_number,
            customer_id=license_obj.customer.id,
            customer_name=license_obj.customer.name,
            customer_tax_id=license_obj.customer.tax_id,
        ))
    
    return log_items

@internal_router.get("/customer/{customer_id}", response_model=List[schemas.LogFileInfo], dependencies=[Depends(security.get_current_active_admin)])
def get_logs_by_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    """
    取得指定客戶的所有 log 檔案（管理員專用）
    """
    # 取得該客戶的所有序號
    licenses = db.query(models.License).options(
        joinedload(models.License.customer)
    ).filter(models.License.customer_id == customer_id).all()
    
    if not licenses:
        raise HTTPException(status_code=404, detail="客戶不存在或沒有授權")
    
    all_logs = []
    for license_obj in licenses:
        log_dir = LOGS_BASE_DIR / license_obj.serial_number
        if log_dir.exists():
            for file_path in log_dir.glob("*.log"):
                stat = file_path.stat()
                # 轉換為台北時區
                uploaded_at_taipei = to_taipei_time(datetime.fromtimestamp(stat.st_mtime))
                all_logs.append(schemas.LogFileInfo(
                    filename=file_path.name,
                    file_size=stat.st_size,
                    uploaded_at=uploaded_at_taipei,
                    serial_number=license_obj.serial_number,
                    customer_id=license_obj.customer.id,
                    customer_name=license_obj.customer.name,
                    customer_tax_id=license_obj.customer.tax_id,
                ))
    
    # 依上傳時間排序（最新的在前）
    all_logs.sort(key=lambda x: x.uploaded_at, reverse=True)
    
    return all_logs

@internal_router.delete("/batch/{batch_id}", dependencies=[Depends(security.get_current_active_admin)])
def delete_batch(
    batch_id: str,
    serial_number: str = Query(..., description="序號"),
    db: Session = Depends(get_db),
):
    """
    刪除指定批次的所有 log 檔案（管理員專用）
    """
    # 驗證序號是否存在
    license_obj = db.query(models.License).filter(
        models.License.serial_number == serial_number
    ).first()
    
    if not license_obj:
        raise HTTPException(status_code=404, detail="序號不存在")
    
    # 取得 log 目錄
    log_dir = LOGS_BASE_DIR / serial_number
    if not log_dir.exists():
        raise HTTPException(status_code=404, detail="該序號沒有 log 檔案")
    
    # 找出該批次的所有檔案（檔名以 {batch_id}_ 開頭）
    deleted_files = []
    failed_files = []
    
    for file_path in log_dir.glob(f"{batch_id}_*.log"):
        try:
            file_path.unlink()
            deleted_files.append(file_path.name)
        except Exception as e:
            logger.error(f"刪除檔案失敗 {file_path.name}: {e}")
            failed_files.append(file_path.name)
    
    if not deleted_files:
        raise HTTPException(status_code=404, detail=f"找不到批次 ID '{batch_id}' 的檔案")
    
    return {
        "status": "success" if not failed_files else "partial",
        "message": f"成功刪除 {len(deleted_files)} 個檔案" + (f"，失敗 {len(failed_files)} 個檔案" if failed_files else ""),
        "deleted_files": deleted_files,
        "failed_files": failed_files
    }

@internal_router.delete("/file", dependencies=[Depends(security.get_current_active_admin)])
def delete_file(
    serial_number: str = Query(..., description="序號"),
    filename: str = Query(..., description="檔案名稱"),
    db: Session = Depends(get_db),
):
    """
    刪除指定的 log 檔案（管理員專用）
    """
    # 驗證序號是否存在
    license_obj = db.query(models.License).filter(
        models.License.serial_number == serial_number
    ).first()
    
    if not license_obj:
        raise HTTPException(status_code=404, detail="序號不存在")
    
    # 取得檔案路徑
    log_dir = LOGS_BASE_DIR / serial_number
    file_path = log_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")
    
    # 驗證檔案在正確的目錄中（防止路徑遍歷攻擊）
    if not file_path.resolve().is_relative_to(log_dir.resolve()):
        raise HTTPException(status_code=403, detail="無效的檔案路徑")
    
    try:
        file_path.unlink()
        return {
            "status": "success",
            "message": f"成功刪除檔案 {filename}"
        }
    except Exception as e:
        logger.error(f"刪除檔案失敗 {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"刪除檔案失敗: {str(e)}")
