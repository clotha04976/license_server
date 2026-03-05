from .base import CRUDBase
from ..models.customer import Customer
from ..schemas import CustomerCreate, CustomerUpdate, CustomerSearchParams, CustomerSearchResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Tuple, Union, Dict, Any

class CRUDCustomer(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
    
    def create(self, db: Session, *, obj_in: CustomerCreate) -> Customer:
        """
        建立客戶，將空字串的 email 轉換為 None
        """
        obj_in_data = obj_in.model_dump()
        # 將空字串轉換為 None，避免唯一性約束錯誤
        if obj_in_data.get('email') == '':
            obj_in_data['email'] = None
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self,
        db: Session,
        *,
        db_obj: Customer,
        obj_in: Union[CustomerUpdate, Dict[str, Any]]
    ) -> Customer:
        """
        更新客戶，將空字串的 email 轉換為 None
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        # 將空字串轉換為 None，避免唯一性約束錯誤
        if 'email' in update_data and update_data['email'] == '':
            update_data['email'] = None
        
        for key, value in update_data.items():
            setattr(db_obj, key, value)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def search_customers(
        self, 
        db: Session, 
        search_params: CustomerSearchParams
    ) -> CustomerSearchResponse:
        """
        搜尋客戶並支援分頁
        """
        query = db.query(Customer)
        
        # 搜尋條件
        if search_params.search:
            search_term = f"%{search_params.search}%"
            query = query.filter(
                or_(
                    Customer.tax_id.ilike(search_term),
                    Customer.name.ilike(search_term),
                    Customer.email.ilike(search_term),
                    Customer.phone.ilike(search_term)
                )
            )
        
        # 排序
        sort_column = getattr(Customer, search_params.sort_by, Customer.id)
        if search_params.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # 計算總數
        total = query.count()
        
        # 分頁
        offset = (search_params.page - 1) * search_params.limit
        items = query.offset(offset).limit(search_params.limit).all()
        
        # 計算總頁數
        total_pages = (total + search_params.limit - 1) // search_params.limit
        
        return CustomerSearchResponse(
            items=items,
            total=total,
            page=search_params.page,
            limit=search_params.limit,
            total_pages=total_pages
        )

customer = CRUDCustomer(Customer)