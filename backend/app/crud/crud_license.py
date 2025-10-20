import uuid
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from .base import CRUDBase
from ..models.license import License
from ..models.customer import Customer
from ..schemas import LicenseCreate, LicenseUpdate, LicenseSearchParams, LicenseSearchResponse

class CRUDLicense(CRUDBase[License, LicenseCreate, LicenseUpdate]):
    def create(self, db: Session, *, obj_in: LicenseCreate) -> License:
        # Generate a unique serial number
        serial_number = f"DUCKY-{uuid.uuid4().hex.upper()[:8]}-{uuid.uuid4().hex.upper()[:8]}"
        
        # Exclude machine_code as it's not part of the License model itself
        create_data = obj_in.model_dump(exclude={'machine_code'})
        db_obj = License(
            **create_data,
            serial_number=serial_number
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, search: Optional[str] = None, status: Optional[str] = None, order_by: str = "created_at_desc"
    ) -> List[License]:
        query = db.query(self.model).options(joinedload(self.model.customer), joinedload(self.model.product))

        if search:
            search_term = f"%{search}%"
            query = query.join(Customer).filter(
                or_(
                    Customer.name.ilike(search_term),
                    Customer.tax_id.ilike(search_term)
                )
            )
        
        if status:
            query = query.filter(self.model.status == status)
        
        # 加入排序邏輯
        if order_by == "created_at_desc":
            query = query.order_by(self.model.created_at.desc())
        elif order_by == "created_at_asc":
            query = query.order_by(self.model.created_at.asc())
        elif order_by == "updated_at_desc":
            query = query.order_by(self.model.updated_at.desc())
        elif order_by == "updated_at_asc":
            query = query.order_by(self.model.updated_at.asc())
        elif order_by == "expires_at_desc":
            query = query.order_by(self.model.expires_at.desc())
        elif order_by == "expires_at_asc":
            query = query.order_by(self.model.expires_at.asc())
        else:
            # 預設按創建時間降序排列
            query = query.order_by(self.model.created_at.desc())
            
        return query.offset(skip).limit(limit).all()

    def search_licenses(
        self, 
        db: Session, 
        search_params: LicenseSearchParams
    ) -> LicenseSearchResponse:
        """
        搜尋授權並支援分頁
        """
        query = db.query(self.model).options(joinedload(self.model.customer), joinedload(self.model.product))

        # 搜尋條件
        if search_params.search:
            search_term = f"%{search_params.search}%"
            query = query.join(Customer).filter(
                or_(
                    Customer.name.ilike(search_term),
                    Customer.tax_id.ilike(search_term)
                )
            )
        
        # 狀態篩選
        if search_params.status:
            query = query.filter(self.model.status == search_params.status)
        
        # 排序
        if search_params.order_by == "created_at_desc":
            query = query.order_by(self.model.created_at.desc())
        elif search_params.order_by == "created_at_asc":
            query = query.order_by(self.model.created_at.asc())
        elif search_params.order_by == "updated_at_desc":
            query = query.order_by(self.model.updated_at.desc())
        elif search_params.order_by == "updated_at_asc":
            query = query.order_by(self.model.updated_at.asc())
        elif search_params.order_by == "expires_at_desc":
            query = query.order_by(self.model.expires_at.desc())
        elif search_params.order_by == "expires_at_asc":
            query = query.order_by(self.model.expires_at.asc())
        else:
            # 預設按創建時間降序排列
            query = query.order_by(self.model.created_at.desc())
        
        # 計算總數
        total = query.count()
        
        # 分頁
        offset = (search_params.page - 1) * search_params.limit
        items = query.offset(offset).limit(search_params.limit).all()
        
        # 計算總頁數
        total_pages = (total + search_params.limit - 1) // search_params.limit
        
        return LicenseSearchResponse(
            items=items,
            total=total,
            page=search_params.page,
            limit=search_params.limit,
            total_pages=total_pages
        )

license = CRUDLicense(License)