from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from pydantic import BaseModel
from urllib.parse import quote
import datetime as dt

from .... import crud, models, schemas
from ....core.dependencies import get_db
from ....services import license_service
from ....core import security

router = APIRouter()

@router.post("/licenses/", response_model=schemas.License, dependencies=[Depends(security.get_current_active_admin)])
def create_license(
    *,
    db: Session = Depends(get_db),
    license_in: schemas.LicenseCreate,
):
    """
    Create new license.
    A unique serial number will be generated automatically.
    """
    customer = crud.customer.get(db=db, id=license_in.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer with id {license_in.customer_id} not found")
    
    product = crud.product.get(db=db, id=license_in.product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id {license_in.product_id} not found")

    license = crud.license.create(db=db, obj_in=license_in)

    if license.status == 'active' and license_in.machine_code:
        active_activations = crud.activation.get_activations_by_license_id(db, license_id=license.id)
        if len(active_activations) < license.max_activations:
            activation_in = schemas.ActivationCreate(
                license_id=license.id,
                machine_code=license_in.machine_code
            )
            crud.activation.create(db=db, obj_in=activation_in)
        else:
            print(f"Warning: License {license.id} created as active, but activation limit was reached. No new activation created.")

    db.refresh(license, attribute_names=['customer', 'product', 'activations'])
    return license

@router.get("/licenses/", response_model=schemas.LicenseSearchResponse, dependencies=[Depends(security.get_current_active_admin)])
def read_licenses(
    db: Session = Depends(get_db),
    search: str = Query(None, description="搜尋關鍵字 (客戶名稱、客戶編號)"),
    status: str = Query(None, description="狀態篩選"),
    order_by: str = Query("created_at_desc", description="排序方式"),
    page: int = Query(1, ge=1, description="頁碼"),
    limit: int = Query(20, ge=1, le=100, description="每頁筆數"),
):
    """
    搜尋和分頁取得授權列表。
    排序選項: created_at_desc, created_at_asc, updated_at_desc, updated_at_asc, expires_at_desc, expires_at_asc
    """
    search_params = schemas.LicenseSearchParams(
        search=search,
        status=status,
        order_by=order_by,
        page=page,
        limit=limit
    )
    return crud.license.search_licenses(db=db, search_params=search_params)

@router.get("/licenses/{license_id}", response_model=schemas.License, dependencies=[Depends(security.get_current_active_admin)])
def read_license_by_id(
    license_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific license by id.
    """
    license = crud.license.get(db=db, id=license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    return license

@router.put("/licenses/{license_id}", response_model=schemas.License, dependencies=[Depends(security.get_current_active_admin)])
def update_license(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    license_in: schemas.LicenseUpdate,
):
    """
    Update a license.
    """
    license = crud.license.get(db=db, id=license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    license = crud.license.update(db=db, db_obj=license, obj_in=license_in)
    return license

@router.post("/licenses/{license_id}/renew", response_model=schemas.License, dependencies=[Depends(security.get_current_active_admin)])
def renew_license(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    
):
    """
    Renew a license for one year.
    If the license is not expired, it adds one year to the current expiry date.
    If the license is expired or has no expiry date, it adds one year from today.
    """
    license = crud.license.get(db=db, id=license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")

    now = datetime.utcnow()
    
    if license.expires_at and license.expires_at > now:
        base_date = license.expires_at
    else:
        base_date = now
        
    new_expiry = base_date.replace(year=base_date.year + 1)
    
    license_update = schemas.LicenseUpdate(expires_at=new_expiry, status='active')
    
    updated_license = crud.license.update(db=db, db_obj=license, obj_in=license_update)
    return updated_license

@router.delete("/licenses/{license_id}", response_model=schemas.License, dependencies=[Depends(security.get_current_active_admin)])
def delete_license(
    *,
    db: Session = Depends(get_db),
    license_id: int,
):
    """
    Delete a license.
    """
    license = crud.license.get(db=db, id=license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    
    deleted_license = crud.license.remove(db=db, id=license_id)
    return deleted_license

class ManualActivationRequest(BaseModel):
    machine_code: str

@router.post("/licenses/{license_id}/activations", response_model=schemas.Activation, dependencies=[Depends(security.get_current_active_admin)])
def add_manual_activation(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    activation_in: ManualActivationRequest,
):
    """
    Manually add an activation record for a license.
    """
    license = crud.license.get(db=db, id=license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")

    # Check activation limit
    active_activations = crud.activation.get_activations_by_license_id(db, license_id=license.id)
    if len(active_activations) >= license.max_activations:
        raise HTTPException(status_code=400, detail="Maximum activation limit reached.")

    activation = crud.activation.create(db, obj_in=schemas.ActivationCreate(
        license_id=license_id,
        machine_code=activation_in.machine_code
    ))
    return activation

@router.get("/licenses/{license_id}/activations", dependencies=[Depends(security.get_current_active_admin)])
def get_license_activations(
    *,
    db: Session = Depends(get_db),
    license_id: int,
):
    """
    Get all activations for a specific license.
    """
    license = crud.license.get(db=db, id=license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    
    activations = db.query(models.Activation).filter(
        models.Activation.license_id == license_id
    ).order_by(models.Activation.activated_at.desc()).all()
    
    return activations

@router.delete("/activations/{activation_id}", dependencies=[Depends(security.get_current_active_admin)])
def delete_activation(
    *,
    db: Session = Depends(get_db),
    activation_id: int,
):
    """
    Delete a specific activation record.
    """
    activation = crud.activation.get(db=db, id=activation_id)
    if not activation:
        raise HTTPException(status_code=404, detail="Activation not found")
    
    # 刪除啟用記錄
    crud.activation.remove(db=db, id=activation_id)
    
    return {"status": "success", "message": "Activation deleted successfully"}

@router.post("/activations/{activation_id}/blacklist", dependencies=[Depends(security.get_current_active_admin)])
def blacklist_activation(
    *,
    db: Session = Depends(get_db),
    activation_id: int,
):
    """
    Add an activation to blacklist.
    """
    activation = crud.activation.get(db=db, id=activation_id)
    if not activation:
        raise HTTPException(status_code=404, detail="Activation not found")
    
    # 檢查授權數量是否合理
    # 計算扣除此啟用記錄後的 active 啟用數量
    current_active_count = crud.activation.count_active_activations_by_license_id(
        db=db, license_id=activation.license_id
    )
    
    # 如果這個啟用記錄是 active 狀態，扣除後數量會減一
    if activation.status == 'active':
        remaining_active_count = current_active_count - 1
    else:
        remaining_active_count = current_active_count
    
    # 取得授權的最大啟用數量
    license_obj = crud.license.get(db=db, id=activation.license_id)
    if not license_obj:
        raise HTTPException(status_code=404, detail="License not found")
    
    # 檢查：如果扣除後，最大啟用數量仍然大於實際啟用數量，則不允許加入黑名單
    if license_obj.max_activations > remaining_active_count:
        raise HTTPException(
            status_code=400, 
            detail=f"無法將此啟用記錄加入黑名單。扣除此記錄後，授權數量({license_obj.max_activations})仍大於已啟用數量({remaining_active_count})，此序號仍可註冊，請先調整授權數量。"
        )
    
    # 將啟用記錄加入黑名單
    activation.status = 'blacklisted'
    activation.blacklisted_at = datetime.utcnow()
    db.add(activation)
    db.commit()
    
    return {"status": "success", "message": "Activation blacklisted successfully"}

# 事件記錄相關 API
@router.get("/event-logs", dependencies=[Depends(security.get_current_active_admin)])
def get_event_logs(
    *,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="頁碼"),
    limit: int = Query(20, ge=1, le=100, description="每頁筆數"),
    serial_number: str = Query(None, description="序號搜尋"),
    customer_name: str = Query(None, description="客戶名稱搜尋"),
    tax_id: str = Query(None, description="客戶編號搜尋"),
    severity: str = Query(None, description="嚴重程度篩選"),
    event_type: str = Query(None, description="事件類型篩選"),
    is_confirmed: bool = Query(None, description="確認狀態篩選"),
    order_by: str = Query("created_at_desc", description="排序方式"),
):
    """
    Get event logs with search and filter options.
    """
    query = db.query(models.EventLog)
    
    # 搜尋條件
    if serial_number:
        query = query.filter(models.EventLog.serial_number.ilike(f"%{serial_number}%"))
    
    if customer_name or tax_id:
        # 需要通過 license 關聯到 customer
        query = query.join(models.License, models.EventLog.license_id == models.License.id)
        query = query.join(models.Customer, models.License.customer_id == models.Customer.id)
        
        if customer_name:
            query = query.filter(models.Customer.name.ilike(f"%{customer_name}%"))
        if tax_id:
            query = query.filter(models.Customer.tax_id.ilike(f"%{tax_id}%"))
    
    # 篩選條件
    if severity:
        query = query.filter(models.EventLog.severity == severity)
    
    if event_type:
        query = query.filter(models.EventLog.event_type == event_type)
    
    if is_confirmed is not None:
        query = query.filter(models.EventLog.is_confirmed == is_confirmed)
    
    # 排序
    if order_by == "created_at_desc":
        query = query.order_by(models.EventLog.created_at.desc())
    elif order_by == "created_at_asc":
        query = query.order_by(models.EventLog.created_at.asc())
    elif order_by == "severity_desc":
        query = query.order_by(models.EventLog.severity.desc())
    elif order_by == "severity_asc":
        query = query.order_by(models.EventLog.severity.asc())
    
    # 分頁
    total = query.count()
    total_pages = (total + limit - 1) // limit
    offset = (page - 1) * limit
    events = query.offset(offset).limit(limit).all()
    
    # 為每個事件添加客戶名稱
    events_with_customer = []
    for event in events:
        event_dict = {
            "id": event.id,
            "license_id": event.license_id,
            "activation_id": event.activation_id,
            "event_type": event.event_type,
            "event_subtype": event.event_subtype,
            "serial_number": event.serial_number,
            "machine_code": event.machine_code,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "details": event.details,
            "severity": event.severity,
            "is_confirmed": event.is_confirmed,
            "confirmed_by": event.confirmed_by,
            "confirmed_at": event.confirmed_at,
            "created_at": event.created_at,
            "customer_name": None
        }
        
        # 獲取客戶名稱
        if event.license_id:
            license_obj = db.query(models.License).filter(models.License.id == event.license_id).first()
            if license_obj and license_obj.customer:
                event_dict["customer_name"] = license_obj.customer.name
        
        events_with_customer.append(event_dict)
    
    return {
        "items": events_with_customer,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }

@router.get("/licenses/{license_id}/download/{machine_code}", response_class=Response, dependencies=[Depends(security.get_current_active_admin)])
def download_license_file(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    machine_code: str,
):
    """
    Download the .lic file for a specific license and machine code.
    """
    license = db.query(models.License).options(
        joinedload(models.License.customer)
    ).filter(models.License.id == license_id).first()
    
    if not license:
        raise HTTPException(status_code=404, detail="License not found")

    try:
        lic_content_bytes = license_service.generate_license_file_content(
            license_obj=license,
            machine_code=machine_code
        )
        today_str = dt.datetime.now().strftime("%Y%m%d")
        filename = f"license_{license.customer.tax_id}_{today_str}.lic"
        encoded_filename = quote(filename)
        
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
        
        return Response(
            content=lic_content_bytes,
            media_type="application/octet-stream",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate license file: {e}")

# 事件管理相關 API
@router.get("/licenses/{license_id}/events", dependencies=[Depends(security.get_current_active_admin)])
def get_license_events(
    *,
    db: Session = Depends(get_db),
    license_id: int,
    limit: int = 50
):
    """獲取指定授權的事件列表"""
    license = crud.license.get(db=db, id=license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    
    events = crud.event_log.get_events_by_serial_number(
        db, serial_number=license.serial_number, limit=limit
    )
    return events

@router.get("/licenses/{license_id}/events/unconfirmed", dependencies=[Depends(security.get_current_active_admin)])
def get_unconfirmed_events(
    *,
    db: Session = Depends(get_db),
    license_id: int
):
    """獲取指定授權的未確認事件"""
    license = crud.license.get(db=db, id=license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    
    events = crud.event_log.get_unconfirmed_events_by_license_id(db, license_id=license_id)
    return events

@router.get("/licenses/{license_id}/events/unconfirmed/count", dependencies=[Depends(security.get_current_active_admin)])
def get_unconfirmed_events_count(
    *,
    db: Session = Depends(get_db),
    license_id: int
):
    """獲取指定授權的未確認事件數量"""
    license = crud.license.get(db=db, id=license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    
    count = crud.event_log.get_unconfirmed_count_by_license_id(db, license_id=license_id)
    return {"count": count}

@router.post("/events/{event_id}/confirm", dependencies=[Depends(security.get_current_active_admin)])
def confirm_event(
    *,
    db: Session = Depends(get_db),
    event_id: int,
    confirmation_request: schemas.EventConfirmationRequest
):
    """確認事件"""
    event = crud.event_log.confirm_event(
        db, event_id=event_id, confirmed_by=confirmation_request.confirmed_by
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event

@router.get("/events/suspicious", dependencies=[Depends(security.get_current_active_admin)])
def get_suspicious_events(
    *,
    db: Session = Depends(get_db),
    days: int = 7,
    limit: int = 100
):
    """獲取可疑事件列表"""
    events = crud.event_log.get_suspicious_events(db, days=days, limit=limit)
    return events