from .base import CRUDBase
from ..models.customer import Customer
from ..schemas import CustomerCreate, CustomerUpdate, CustomerSearchParams, CustomerSearchResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Tuple

class CRUDCustomer(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
    
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