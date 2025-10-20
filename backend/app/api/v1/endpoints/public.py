from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app import crud, models, schemas
from app.core.dependencies import get_db
from app.services import license_service
from app.core.rate_limiter import limiter

router = APIRouter()

@router.get("/health")
@limiter.limit("120/minute")
def health_check(request: Request):
    """
    Health check endpoint to verify API is running.
    """
    # 使用 UTC 時間，避免洩露時區資訊
    current_time = datetime.utcnow()
    
    return {
        "status": "ok", 
        "message": "Public API is healthy",
        "timestamp": current_time.isoformat() + "Z",  # ISO 格式，明確標示 UTC
        "uptime_check": True
    }

class ActivationRequest(BaseModel):
    serial_number: str
    machine_code: str
    keypro_id: Optional[str] = None
    motherboard_id: Optional[str] = None
    disk_id: Optional[str] = None

@router.post("/activate")
@limiter.limit("10/minute")
async def activate_license(
    request: Request,
    activation_in: ActivationRequest = Body(...),
    db: Session = Depends(get_db),
):
    """
    Activate a license with a serial number and machine code.
    """
    print(await request.body())
    license_obj = db.query(models.License).filter(models.License.serial_number == activation_in.serial_number).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="Serial number not found.")

    if license_obj.status not in ['active', 'pending']:
        raise HTTPException(status_code=400, detail=f"License status is {license_obj.status} and cannot be activated.")

    if license_obj.expires_at and license_obj.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="License has expired.")

    active_activations = crud.activation.get_activations_by_license_id(db, license_id=license_obj.id)
    machine_code_prefix = activation_in.machine_code[:16] if len(activation_in.machine_code) >= 16 else activation_in.machine_code
    is_already_activated = any(act.machine_code.startswith(machine_code_prefix) for act in active_activations)

    if len(active_activations) >= license_obj.max_activations and not is_already_activated:
        raise HTTPException(
            status_code=403, 
            detail="Maximum activation limit reached for this serial number."
        )

    existing_activation = None

    # 1. 先檢查是否有相同的 machine_code (前16碼)
    machine_code_prefix = activation_in.machine_code[:16] if len(activation_in.machine_code) >= 16 else activation_in.machine_code
    existing_activation = db.query(models.Activation).filter(
        models.Activation.license_id == license_obj.id,
        models.Activation.machine_code.like(f"{machine_code_prefix}%")
    ).first()

    # 2. 如果沒有找到相同的 machine_code，檢查硬體ID匹配
    if not existing_activation and (activation_in.keypro_id or activation_in.motherboard_id or activation_in.disk_id):
        query = db.query(models.Activation).filter(
            models.Activation.license_id == license_obj.id,
            models.Activation.status == 'active'
        )
        
        conditions = []
        if activation_in.keypro_id:
            conditions.append(models.Activation.keypro_id == activation_in.keypro_id)
        if activation_in.motherboard_id:
            conditions.append(models.Activation.motherboard_id == activation_in.motherboard_id)
        if activation_in.disk_id:
            conditions.append(models.Activation.disk_id == activation_in.disk_id)
        
        if conditions:
            from sqlalchemy import or_
            existing_activation = query.filter(or_(*conditions)).first()
            
            # 如果找到匹配的硬體ID，更新機器碼
            if existing_activation:
                existing_activation.machine_code = activation_in.machine_code
                print(f"Updated machine code for license {license_obj.serial_number} due to hardware match")

    if not existing_activation:
        # 建立新的啟用記錄，包含硬體ID資訊
        activation_create_data = {
            "license_id": license_obj.id,
            "machine_code": activation_in.machine_code
        }
        
        # 添加硬體ID資訊（包括 None 值以明確標記不存在的硬體）
        activation_create_data["keypro_id"] = activation_in.keypro_id
        activation_create_data["motherboard_id"] = activation_in.motherboard_id
        activation_create_data["disk_id"] = activation_in.disk_id
            
        new_activation = crud.activation.create(db, obj_in=schemas.ActivationCreate(**activation_create_data))
        
        # 記錄新啟用事件
        event_data = {
            "license_id": license_obj.id,
            "activation_id": new_activation.id,
            "event_type": "activation",
            "event_subtype": "new_activation",
            "serial_number": license_obj.serial_number,
            "machine_code": activation_in.machine_code,
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "details": {
                "hardware_ids": {
                    "keypro_id": activation_in.keypro_id,
                    "motherboard_id": activation_in.motherboard_id,
                    "disk_id": activation_in.disk_id
                }
            },
            "severity": "info"
        }
        crud.event_log.create(db, obj_in=schemas.EventLogCreate(**event_data))
    else:
        # 檢查是否為重複啟用或硬體變化
        is_hardware_match = existing_activation.machine_code != activation_in.machine_code
        is_hardware_change = (
            existing_activation.keypro_id != activation_in.keypro_id or
            existing_activation.motherboard_id != activation_in.motherboard_id or
            existing_activation.disk_id != activation_in.disk_id
        )
        
        # 更新現有啟用記錄的硬體ID資訊（包括 None 值以清除硬體ID）
        update_data = {
            "keypro_id": activation_in.keypro_id,
            "motherboard_id": activation_in.motherboard_id,
            "disk_id": activation_in.disk_id
        }
        crud.activation.update(db, db_obj=existing_activation, obj_in=update_data)
        
        # 記錄重複啟用事件
        event_type = "re_activation"
        event_subtype = "machine_code_match"
        severity = "suspicious"
        details = {}
        
        if is_hardware_match:
            event_subtype = "hardware_id_match"
            details = {
                "old_machine_code": existing_activation.machine_code,
                "new_machine_code": activation_in.machine_code,
                "hardware_changes": {
                    "keypro_id": {"old": existing_activation.keypro_id, "new": activation_in.keypro_id},
                    "motherboard_id": {"old": existing_activation.motherboard_id, "new": activation_in.motherboard_id},
                    "disk_id": {"old": existing_activation.disk_id, "new": activation_in.disk_id}
                }
            }
        elif is_hardware_change:
            event_subtype = "hardware_change"
            details = {
                "hardware_changes": {
                    "keypro_id": {"old": existing_activation.keypro_id, "new": activation_in.keypro_id},
                    "motherboard_id": {"old": existing_activation.motherboard_id, "new": activation_in.motherboard_id},
                    "disk_id": {"old": existing_activation.disk_id, "new": activation_in.disk_id}
                }
            }
        else:
            event_subtype = "machine_code_match"
            severity = "info"
        
        event_data = {
            "license_id": license_obj.id,
            "activation_id": existing_activation.id,
            "event_type": event_type,
            "event_subtype": event_subtype,
            "serial_number": license_obj.serial_number,
            "machine_code": activation_in.machine_code,
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "details": details,
            "severity": severity
        }
        crud.event_log.create(db, obj_in=schemas.EventLogCreate(**event_data))
    
    if license_obj.status == 'pending':
        license_obj.status = 'active'
        db.add(license_obj)
        db.commit()
        db.refresh(license_obj)

    try:
        # 準備硬體ID資訊
        hardware_ids = {}
        if activation_in.keypro_id:
            hardware_ids["keypro"] = activation_in.keypro_id
        if activation_in.motherboard_id:
            hardware_ids["motherboard"] = activation_in.motherboard_id
        if activation_in.disk_id:
            hardware_ids["disk"] = activation_in.disk_id
            
        lic_content_bytes = license_service.generate_license_file_content(
            license_obj=license_obj,
            machine_code=activation_in.machine_code,
            hardware_ids=hardware_ids if hardware_ids else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate license file")

    return {
        "status": "success", 
        "message": "License activated successfully.",
        "license_file_content": lic_content_bytes.decode('utf-8')
    }

@router.post("/deactivate")
@limiter.limit("1/minute")
async def deactivate_license(
    request: Request,
    activation_in: ActivationRequest = Body(...),
    db: Session = Depends(get_db),
):
    """
    Deactivate a license for a specific machine.
    """
    print(await request.body())
    license_obj = db.query(models.License).filter(models.License.serial_number == activation_in.serial_number).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="Serial number not found.")

    activation_obj = db.query(models.Activation).filter(
        models.Activation.license_id == license_obj.id,
        models.Activation.machine_code == activation_in.machine_code,
        models.Activation.status == 'active'
    ).first()

    if not activation_obj:
        raise HTTPException(status_code=404, detail="No active license found for this machine.")

    db.delete(activation_obj)
    db.commit()

    remaining_activations = db.query(models.Activation).filter(
        models.Activation.license_id == license_obj.id,
        models.Activation.status == 'active'
    ).count()

    if remaining_activations == 0:
        license_obj.status = 'pending'
        db.add(license_obj)
        db.commit()
        db.refresh(license_obj)

    return {"status": "success", "message": "License deactivated and freed up successfully."}

@router.post("/validate")
@limiter.limit("30/minute", methods=["POST"])
async def validate_license(
    request: Request,
    activation_in: ActivationRequest = Body(...),
    db: Session = Depends(get_db),
):
    """
    Validate an existing activation and get the latest license file.
    """
    print(await request.body())
    license_obj = db.query(models.License).filter(models.License.serial_number == activation_in.serial_number).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="Serial number not found.")

    # 1. 首先檢查是否有黑名單的啟用記錄
    # 檢查機器碼匹配的黑名單記錄
    blacklisted_activation = db.query(models.Activation).filter(
        models.Activation.license_id == license_obj.id,
        models.Activation.machine_code == activation_in.machine_code,
        models.Activation.motherboard_id == activation_in.motherboard_id,
        models.Activation.disk_id == activation_in.disk_id,
        models.Activation.status == 'blacklisted'
    ).first()
    
    # 如果沒有機器碼匹配的黑名單記錄，檢查硬體ID匹配
    if not blacklisted_activation and (activation_in.keypro_id or activation_in.motherboard_id or activation_in.disk_id):
        query = db.query(models.Activation).filter(
            models.Activation.license_id == license_obj.id,
            models.Activation.status == 'blacklisted'
        )
        
        conditions = []
        ambiguous_disk_id = ['Volume', 'DAHA']
        if activation_in.keypro_id:
            conditions.append(models.Activation.keypro_id == activation_in.keypro_id)
        if activation_in.motherboard_id:
            conditions.append(models.Activation.motherboard_id == activation_in.motherboard_id)
        if activation_in.disk_id and any(id_part in activation_in.disk_id for id_part in ambiguous_disk_id):
            conditions.append(models.Activation.disk_id == activation_in.disk_id)
        
        if conditions:
            from sqlalchemy import or_
            blacklisted_activation = query.filter(or_(*conditions)).first()
    
    if blacklisted_activation:
        raise HTTPException(status_code=403, detail="此電腦已被列入取消清單，無法驗證授權。")

    # 2. 尋找現有的啟用記錄
    activation_obj = db.query(models.Activation).filter(
        models.Activation.license_id == license_obj.id,
        models.Activation.machine_code == activation_in.machine_code,
        models.Activation.status == 'active'
    ).first()

    # 3. 如果找不到對應的 machine_code，檢查是否有硬體ID匹配
    if not activation_obj and (activation_in.keypro_id or activation_in.motherboard_id or activation_in.disk_id):
        # 尋找有任何硬體ID匹配的啟用記錄
        query = db.query(models.Activation).filter(
            models.Activation.license_id == license_obj.id,
            models.Activation.status == 'active'
        )
        
        conditions = []
        ambiguous_disk_id = ['Volume_0000', 'Volume_0001', 'Volume_0002', 'Volume_0003', 'DAHA']
        if activation_in.keypro_id:
            conditions.append(models.Activation.keypro_id == activation_in.keypro_id)
        if activation_in.motherboard_id:
            conditions.append(models.Activation.motherboard_id == activation_in.motherboard_id)
        if activation_in.disk_id and activation_in.disk_id not in ambiguous_disk_id:
            conditions.append(models.Activation.disk_id == activation_in.disk_id)
        
        if conditions:
            from sqlalchemy import or_
            activation_obj = query.filter(or_(*conditions)).first()
            
            # 如果找到匹配的硬體ID，創建新的啟用記錄而不是更新現有的
            if activation_obj:
                # 停用舊的啟用記錄
                activation_obj.status = 'deactivated'
                activation_obj.deactivated_at = datetime.utcnow()
                db.add(activation_obj)
                
                # 創建新的啟用記錄
                new_activation = models.Activation(
                    license_id=license_obj.id,
                    machine_code=activation_in.machine_code,
                    keypro_id=activation_in.keypro_id,
                    motherboard_id=activation_in.motherboard_id,
                    disk_id=activation_in.disk_id,
                    ip_address=request.client.host,
                    status='active',
                    activated_at=datetime.utcnow()
                )
                db.add(new_activation)
                db.commit()
                
                activation_obj = new_activation
                print(f"Created new activation for license {license_obj.serial_number} due to hardware change")

    if not activation_obj:
        raise HTTPException(status_code=403, detail="序號與電腦配對失敗。")

    if license_obj.status != 'active':
        raise HTTPException(status_code=403, detail="授權已不再有效。")

    activation_obj.last_validated_at = datetime.utcnow()
    activation_obj.ip_address = request.client.host
    db.add(activation_obj)
    db.commit()

    try:
        # 準備硬體ID資訊
        hardware_ids = {}
        if activation_in.keypro_id or activation_obj.keypro_id:
            hardware_ids["keypro"] = activation_in.keypro_id or activation_obj.keypro_id
        if activation_in.motherboard_id or activation_obj.motherboard_id:
            hardware_ids["motherboard"] = activation_in.motherboard_id or activation_obj.motherboard_id
        if activation_in.disk_id or activation_obj.disk_id:
            hardware_ids["disk"] = activation_in.disk_id or activation_obj.disk_id
            
        lic_content_bytes = license_service.generate_license_file_content(
            license_obj=license_obj,
            machine_code=activation_obj.machine_code,  # 使用可能已更新的 machine_code
            hardware_ids=hardware_ids if hardware_ids else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="授權檔案生成失敗。")

    # 檢查是否有硬體變化需要更新
    machine_code_updated = activation_obj.machine_code != activation_in.machine_code
    hardware_updated = (
        (activation_in.keypro_id and activation_in.keypro_id != activation_obj.keypro_id) or
        (activation_in.motherboard_id and activation_in.motherboard_id != activation_obj.motherboard_id) or
        (activation_in.disk_id and activation_in.disk_id != activation_obj.disk_id)
    )

    response_data = {
        "status": "success",
        "message": "授權驗證成功。",
        "license_file_content": lic_content_bytes.decode('utf-8')
    }
    
    # 記錄正常驗證事件（預設已確認）
    validation_event_data = {
        "license_id": license_obj.id,
        "activation_id": activation_obj.id,
        "event_type": "validation",
        "event_subtype": "normal_validation",
        "serial_number": license_obj.serial_number,
        "machine_code": activation_in.machine_code,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "details": {
            "validation_successful": True,
            "hardware_ids": {
                "keypro_id": activation_in.keypro_id,
                "motherboard_id": activation_in.motherboard_id,
                "disk_id": activation_in.disk_id
            }
        },
        "severity": "info",
        "is_confirmed": True,  # 正常驗證預設已確認
        "confirmed_by": "system",
        "confirmed_at": datetime.utcnow()
    }
    crud.event_log.create(db, obj_in=schemas.EventLogCreate(**validation_event_data))
    
    # 如果有硬體變化，添加更新標記並記錄事件
    if machine_code_updated or hardware_updated:
        response_data["hardware_updated"] = True
        response_data["message"] = "授權驗證成功。檢測到硬體變化，授權檔案已更新。"
        
        # 記錄硬體變化事件
        event_data = {
            "license_id": license_obj.id,
            "activation_id": activation_obj.id,
            "event_type": "hardware_change",
            "event_subtype": "validation_hardware_change",
            "serial_number": license_obj.serial_number,
            "machine_code": activation_in.machine_code,
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "details": {
                "machine_code_updated": machine_code_updated,
                "hardware_updated": hardware_updated,
                "hardware_changes": {
                    "keypro_id": {"old": activation_obj.keypro_id, "new": activation_in.keypro_id},
                    "motherboard_id": {"old": activation_obj.motherboard_id, "new": activation_in.motherboard_id},
                    "disk_id": {"old": activation_obj.disk_id, "new": activation_in.disk_id}
                }
            },
            "severity": "suspicious"
        }
        crud.event_log.create(db, obj_in=schemas.EventLogCreate(**event_data))
    
    return response_data