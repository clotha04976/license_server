from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from sqlalchemy.orm import joinedload
from .... import crud, models, schemas
from ....core.dependencies import get_db
from ....core import security

router = APIRouter()

@router.post("/", response_model=schemas.Customer, dependencies=[Depends(security.get_current_active_admin)])
def create_customer(
    *,
    db: Session = Depends(get_db),
    customer_in: schemas.CustomerCreate,
):
    """
    Create new customer.
    """
    customer = crud.customer.create(db=db, obj_in=customer_in)
    return customer

@router.get("/", response_model=schemas.CustomerSearchResponse, dependencies=[Depends(security.get_current_active_admin)])
def read_customers(
    db: Session = Depends(get_db),
    search: str = Query(None, description="搜尋關鍵字 (客戶編號、公司名稱、email、電話)"),
    page: int = Query(1, ge=1, description="頁碼"),
    limit: int = Query(20, ge=1, le=100, description="每頁筆數"),
    sort_by: str = Query("id", description="排序欄位"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="排序方向"),
):
    """
    搜尋和分頁取得客戶列表。
    """
    search_params = schemas.CustomerSearchParams(
        search=search,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return crud.customer.search_customers(db=db, search_params=search_params)

@router.get("/{customer_id}", response_model=schemas.Customer, dependencies=[Depends(security.get_current_active_admin)])
def read_customer_by_id(
    customer_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific customer by id.
    """
    customer = crud.customer.get(db=db, id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.put("/{customer_id}", response_model=schemas.Customer, dependencies=[Depends(security.get_current_active_admin)])
def update_customer(
    *,
    db: Session = Depends(get_db),
    customer_id: int,
    customer_in: schemas.CustomerUpdate,
):
    """
    Update a customer.
    """
    customer = crud.customer.get(db=db, id=customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer = crud.customer.update(db=db, db_obj=customer, obj_in=customer_in)
    return customer

@router.delete("/{customer_id}", response_model=schemas.Customer, dependencies=[Depends(security.get_current_active_admin)])
def delete_customer(
    *,
    db: Session = Depends(get_db),
    customer_id: int,
):
    """
    Delete a customer.
    """
    customer = db.query(models.Customer).options(
        joinedload(models.Customer.licenses)
    ).filter(models.Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    deleted_customer = crud.customer.remove(db=db, id=customer_id)
    return customer