from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app import crud, models, schemas
from app.core.dependencies import get_db
from app.core.utils import get_real_ip
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
    app_version: Optional[str] = None

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
        # 不可用的 disk_id 名單 - 可以自行增加
        blacklisted_disk_ids = ['DAHA']  # 其他不可用的 ID 可以加在這裡
        
        def is_valid_disk_id(disk_id: str) -> bool:
            """檢查 disk_id 是否有效
            - 以 'Volume' 開頭的 ID 視為無意義
            - 在黑名單中的 ID 也視為無意義
            """
            if not disk_id:
                return False
            # 檢查是否以 Volume 開頭
            if disk_id.startswith('Volume'):
                return False
            # 檢查是否在黑名單中
            if disk_id in blacklisted_disk_ids:
                return False
            return True
        
        query = db.query(models.Activation).filter(
            models.Activation.license_id == license_obj.id,
            models.Activation.status == 'active'
        )
        
        conditions = []
        if activation_in.keypro_id:
            conditions.append(models.Activation.keypro_id == activation_in.keypro_id)
        if activation_in.motherboard_id:
            conditions.append(models.Activation.motherboard_id == activation_in.motherboard_id)
        if activation_in.disk_id and is_valid_disk_id(activation_in.disk_id):
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
        activation_create_data["app_version"] = activation_in.app_version
            
        new_activation = crud.activation.create(db, obj_in=schemas.ActivationCreate(**activation_create_data))
        
        # 記錄新啟用事件
        event_data = {
            "license_id": license_obj.id,
            "activation_id": new_activation.id,
            "event_type": "activation",
            "event_subtype": "new_activation",
            "serial_number": license_obj.serial_number,
            "machine_code": activation_in.machine_code,
            "ip_address": get_real_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "details": {
                "hardware_ids": {
                    "keypro_id": activation_in.keypro_id,
                    "motherboard_id": activation_in.motherboard_id,
                    "disk_id": activation_in.disk_id
                },
                "app_version": activation_in.app_version
            },
            "severity": "info"
        }
        crud.event_log.create(db, obj_in=schemas.EventLogCreate(**event_data))
    else:
        # 檢查 keypro_id 限制：如果序號已經有 keypro_id，且新的 keypro_id 不同，則禁止
        if activation_in.keypro_id and existing_activation.keypro_id and existing_activation.keypro_id != activation_in.keypro_id:
            raise HTTPException(
                status_code=403, 
                detail=f"此序號已綁定其他 KeyPro，無法更換，如需要更換，請聯繫客服。"
            )
        
        # 檢查是否為重複啟用或硬體變化
        machine_code_changed = existing_activation.machine_code != activation_in.machine_code
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
        event_subtype = "no_change"
        severity = "info"
        details = {}
        
        # 檢查是否有任何變化
        if machine_code_changed or is_hardware_change:
            severity = "suspicious"
            
            if machine_code_changed and is_hardware_change:
                event_subtype = "machine_code_and_hardware_change"
                details = {
                    "machine_code_changed": True,
                    "old_machine_code": existing_activation.machine_code,
                    "new_machine_code": activation_in.machine_code,
                    "hardware_changes": {
                        "keypro_id": {"old": existing_activation.keypro_id, "new": activation_in.keypro_id},
                        "motherboard_id": {"old": existing_activation.motherboard_id, "new": activation_in.motherboard_id},
                        "disk_id": {"old": existing_activation.disk_id, "new": activation_in.disk_id}
                    },
                    "app_version": {"old": existing_activation.app_version, "new": activation_in.app_version}
                }
            elif machine_code_changed:
                event_subtype = "machine_code_change"
                details = {
                    "machine_code_changed": True,
                    "old_machine_code": existing_activation.machine_code,
                    "new_machine_code": activation_in.machine_code,
                    "hardware_changes": {
                        "keypro_id": {"old": existing_activation.keypro_id, "new": activation_in.keypro_id},
                        "motherboard_id": {"old": existing_activation.motherboard_id, "new": activation_in.motherboard_id},
                        "disk_id": {"old": existing_activation.disk_id, "new": activation_in.disk_id}
                    },
                    "app_version": {"old": existing_activation.app_version, "new": activation_in.app_version}
                }
            elif is_hardware_change:
                event_subtype = "hardware_change"
                details = {
                    "machine_code_changed": False,
                    "hardware_changes": {
                        "keypro_id": {"old": existing_activation.keypro_id, "new": activation_in.keypro_id},
                        "motherboard_id": {"old": existing_activation.motherboard_id, "new": activation_in.motherboard_id},
                        "disk_id": {"old": existing_activation.disk_id, "new": activation_in.disk_id}
                    },
                    "app_version": {"old": existing_activation.app_version, "new": activation_in.app_version}
                }
        else:
            # 完全沒有變化
            event_subtype = "no_change"
            severity = "info"
            details = {
                "machine_code_changed": False,
                "hardware_changes": {
                    "keypro_id": {"old": existing_activation.keypro_id, "new": activation_in.keypro_id},
                    "motherboard_id": {"old": existing_activation.motherboard_id, "new": activation_in.motherboard_id},
                    "disk_id": {"old": existing_activation.disk_id, "new": activation_in.disk_id}
                },
                "app_version": {"old": existing_activation.app_version, "new": activation_in.app_version}
            }
        
        event_data = {
            "license_id": license_obj.id,
            "activation_id": existing_activation.id,
            "event_type": event_type,
            "event_subtype": event_subtype,
            "serial_number": license_obj.serial_number,
            "machine_code": activation_in.machine_code,
            "ip_address": get_real_ip(request),
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
            hardware_ids=hardware_ids if hardware_ids else None,
            app_version=activation_in.app_version
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
        # 首先檢查 keypro_id 限制：如果序號已經有 keypro_id，且新的 keypro_id 不同，則禁止
        if activation_in.keypro_id:
            existing_keypro = db.query(models.Activation).filter(
                models.Activation.license_id == license_obj.id,
                models.Activation.status == 'active',
                models.Activation.keypro_id.isnot(None),
                models.Activation.keypro_id != activation_in.keypro_id
            ).first()
            
            if existing_keypro:
                raise HTTPException(
                    status_code=403, 
                    detail=f"此序號已綁定其他 KeyPro，無法更換，如需要更換，請聯繫客服。"
                )
        
        # 尋找有任何硬體ID匹配的啟用記錄
        query = db.query(models.Activation).filter(
            models.Activation.license_id == license_obj.id,
            models.Activation.status == 'active'
        )
        
        conditions = []
        # 不可用的 disk_id 名單 - 可以自行增加
        blacklisted_disk_ids = ['DAHA']  # 其他不可用的 ID 可以加在這裡
        
        def is_valid_disk_id(disk_id: str) -> bool:
            """檢查 disk_id 是否有效
            - 以 'Volume' 開頭的 ID 視為無意義
            - 在黑名單中的 ID 也視為無意義
            """
            if not disk_id:
                return False
            # 檢查是否以 Volume 開頭
            if disk_id.startswith('Volume'):
                return False
            # 檢查是否在黑名單中
            if disk_id in blacklisted_disk_ids:
                return False
            return True
        
        if activation_in.keypro_id:
            conditions.append(models.Activation.keypro_id == activation_in.keypro_id)
        if activation_in.motherboard_id:
            conditions.append(models.Activation.motherboard_id == activation_in.motherboard_id)
        if activation_in.disk_id and is_valid_disk_id(activation_in.disk_id):
            conditions.append(models.Activation.disk_id == activation_in.disk_id)
        
        if conditions:
            from sqlalchemy import or_
            activation_obj = query.filter(or_(*conditions)).first()
            
            # 如果找到匹配的硬體ID，創建新的啟用記錄而不是更新現有的
            if activation_obj:
                # 保存原始資訊用於後續比較
                original_machine_code = activation_obj.machine_code
                original_keypro_id = activation_obj.keypro_id
                original_motherboard_id = activation_obj.motherboard_id
                original_disk_id = activation_obj.disk_id
                original_app_version = activation_obj.app_version
                
                # 停用舊的啟用記錄
                activation_obj.status = 'deactivated'
                activation_obj.deactivated_at = datetime.utcnow()
                db.add(activation_obj)
                
                # 創建新的啟用記錄
                # 如果原本的啟用記錄有 keypro_id，但新的請求中沒有 keypro_id，
                # 則保持原本的 keypro_id，不設為 null
                preserved_keypro_id = activation_in.keypro_id
                if not activation_in.keypro_id and original_keypro_id:
                    preserved_keypro_id = original_keypro_id
                
                new_activation = models.Activation(
                    license_id=license_obj.id,
                    machine_code=activation_in.machine_code,
                    keypro_id=preserved_keypro_id,
                    motherboard_id=activation_in.motherboard_id,
                    disk_id=activation_in.disk_id,
                    app_version=activation_in.app_version,
                    ip_address=get_real_ip(request),
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
    activation_obj.ip_address = get_real_ip(request)
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
            
        # 檢測 Keypro 降級情況
        activation_keypro = activation_obj.keypro_id
        request_keypro = activation_in.keypro_id
        invalid_keypro_values = [None, '', 'NO_KEYPRO', 'None', 'Unknown']
        
        if activation_keypro and activation_keypro not in invalid_keypro_values and \
           (not request_keypro or request_keypro in invalid_keypro_values):
            # Keypro 遺失，檢查硬體匹配
            disk_match = (activation_obj.disk_id and activation_in.disk_id and 
                         activation_obj.disk_id == activation_in.disk_id)
            motherboard_match = (activation_obj.motherboard_id and activation_in.motherboard_id and 
                                activation_obj.motherboard_id == activation_in.motherboard_id)
            
            if disk_match or motherboard_match:
                # 允許降級，生成授權時加入 degraded_at
                hardware_ids["degraded_at"] = datetime.utcnow().isoformat() + "Z"
            
        lic_content_bytes = license_service.generate_license_file_content(
            license_obj=license_obj,
            machine_code=activation_obj.machine_code,  # 使用可能已更新的 machine_code
            hardware_ids=hardware_ids if hardware_ids else None,
            app_version=activation_in.app_version  # 傳遞應用程式版本
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="授權檔案生成失敗。")

    # 檢查是否有硬體變化需要更新
    # 如果是在硬體ID匹配情況下創建的新啟用記錄，使用原始資訊進行比較
    if 'original_machine_code' in locals():
        machine_code_updated = original_machine_code != activation_in.machine_code
        hardware_updated = (
            (activation_in.keypro_id and activation_in.keypro_id != original_keypro_id) or
            (activation_in.motherboard_id and activation_in.motherboard_id != original_motherboard_id) or
            (activation_in.disk_id and activation_in.disk_id != original_disk_id)
        )
    else:
        # 正常情況下的比較
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
        "ip_address": get_real_ip(request),
        "user_agent": request.headers.get("user-agent"),
        "details": {
            "validation_successful": True,
            "hardware_ids": {
                "keypro_id": activation_in.keypro_id,
                "motherboard_id": activation_in.motherboard_id,
                "disk_id": activation_in.disk_id
            },
            "app_version": activation_in.app_version
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
            "ip_address": get_real_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "details": {
                "machine_code_updated": machine_code_updated,
                "hardware_updated": hardware_updated,
                "hardware_changes": {
                    "keypro_id": {"old": original_keypro_id if 'original_keypro_id' in locals() else activation_obj.keypro_id, "new": activation_in.keypro_id},
                    "motherboard_id": {"old": original_motherboard_id if 'original_motherboard_id' in locals() else activation_obj.motherboard_id, "new": activation_in.motherboard_id},
                    "disk_id": {"old": original_disk_id if 'original_disk_id' in locals() else activation_obj.disk_id, "new": activation_in.disk_id}
                },
                "app_version": {"old": original_app_version if 'original_app_version' in locals() else activation_obj.app_version, "new": activation_in.app_version}
            },
            "severity": "suspicious"
        }
        crud.event_log.create(db, obj_in=schemas.EventLogCreate(**event_data))
    
    return response_data