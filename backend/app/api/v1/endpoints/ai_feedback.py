from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
import os
import csv
import shutil
from pathlib import Path
import logging
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

from .... import models, schemas
from ....core.dependencies import get_db

# Public router（只有上傳端點，給客戶端 opt-in 蒐集用）
public_router = APIRouter()

# AI 回饋資料儲存根目錄（沿用 training_data 的 dataset_to_train volume）
_is_docker = os.path.exists("/app/app")
_default_dataset_dir = "/app/dataset_to_train" if _is_docker else str(
    Path(__file__).parent.parent.parent.parent.parent / "dataset_to_train"
)
DATASET_BASE_DIR = Path(os.getenv("DATASET_DIR", _default_dataset_dir))
AI_FEEDBACK_BASE_DIR = DATASET_BASE_DIR / "ai_feedback"
AI_FEEDBACK_BASE_DIR.mkdir(parents=True, exist_ok=True)
logger.info(f"AI 回饋資料儲存目錄: {AI_FEEDBACK_BASE_DIR.resolve()}")

# 台北時區
TAIPEI_TZ = ZoneInfo("Asia/Taipei")

# 允許的回饋類型 -> 子目錄
ALLOWED_FEEDBACK_TYPES = {"screenshot", "number_correction"}

# labels.csv 欄位
CSV_FIELDS = [
    "stored_filename",
    "ocr_result",
    "corrected_number",
    "mode",
    "app_version",
    "client_timestamp",
    "server_timestamp",
]


def get_feedback_dir(serial_number: str, feedback_type: str) -> Path:
    """取得指定序號 + 回饋類型的儲存目錄"""
    feedback_dir = AI_FEEDBACK_BASE_DIR / serial_number / feedback_type
    feedback_dir.mkdir(parents=True, exist_ok=True)
    return feedback_dir


@public_router.post("/upload", response_model=schemas.AiFeedbackUploadResponse)
async def upload_ai_feedback(
    serial_number: str = Form(...),
    feedback_type: str = Form(...),
    mode: str = Form(""),
    ocr_result: str = Form(""),
    corrected_number: str = Form(""),
    app_version: str = Form(""),
    client_timestamp: str = Form(""),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    接收客戶端 opt-in 上傳的 AI 訓練回饋影像。
    - 驗證序號是否存在於資料庫
    - 依 feedback_type 分目錄儲存：ai_feedback/{serial}/{feedback_type}/
    - append 一列到 labels.csv 記錄標籤
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

    # 驗證回饋類型
    if feedback_type not in ALLOWED_FEEDBACK_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"未知的 feedback_type '{feedback_type}'，"
                   f"允許值：{sorted(ALLOWED_FEEDBACK_TYPES)}"
        )

    feedback_dir = get_feedback_dir(serial_number, feedback_type)

    # 產生儲存檔名：{server_ts}_{原始檔名}
    server_dt = datetime.now(TAIPEI_TZ)
    server_ts = server_dt.strftime("%Y%m%d_%H%M%S_%f")
    raw_name = image.filename or "image.jpg"
    safe_name = raw_name.replace("\\", "_").replace("/", "_")
    stored_filename = f"{server_ts}_{safe_name}"
    image_path = feedback_dir / stored_filename

    try:
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        logger.error(f"儲存 AI 回饋影像失敗 {stored_filename}: {e}")
        raise HTTPException(status_code=500, detail=f"儲存影像失敗: {e}")

    # append 標籤到 labels.csv
    csv_path = feedback_dir / "labels.csv"
    write_header = not csv_path.exists()
    try:
        with open(csv_path, "a", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow({
                "stored_filename": stored_filename,
                "ocr_result": ocr_result,
                "corrected_number": corrected_number,
                "mode": mode,
                "app_version": app_version,
                "client_timestamp": client_timestamp,
                "server_timestamp": server_dt.isoformat(),
            })
    except Exception as e:
        # 影像已存，但標籤寫入失敗只記 log，不讓整個請求失敗
        logger.warning(f"寫入 labels.csv 失敗 {csv_path}: {e}")

    logger.info(f"AI 回饋已儲存: {image_path} (type={feedback_type})")
    return schemas.AiFeedbackUploadResponse(
        status="success",
        message="AI 回饋影像已儲存",
        stored_filename=stored_filename,
    )
