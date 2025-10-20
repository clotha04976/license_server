from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from sqlalchemy.orm import joinedload
from .... import crud, models, schemas
from ....core.dependencies import get_db
from ....core import security

router = APIRouter()

@router.post("/", response_model=schemas.Product, dependencies=[Depends(security.get_current_active_admin)])
def create_product(
    *,
    db: Session = Depends(get_db),
    product_in: schemas.ProductCreate,
):
    """
    Create new product.
    """
    product = crud.product.create(db=db, obj_in=product_in)
    return product

@router.get("/", response_model=List[schemas.Product], dependencies=[Depends(security.get_current_active_admin)])
def read_products(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve products.
    """
    products = crud.product.get_multi(db, skip=skip, limit=limit)
    return products

@router.get("/{product_id}", response_model=schemas.Product, dependencies=[Depends(security.get_current_active_admin)])
def read_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific product by id.
    """
    product = crud.product.get(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=schemas.Product, dependencies=[Depends(security.get_current_active_admin)])
def update_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    product_in: schemas.ProductUpdate,
):
    """
    Update a product.
    """
    product = crud.product.get(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product = crud.product.update(db=db, db_obj=product, obj_in=product_in)
    return product

@router.delete("/{product_id}", response_model=schemas.Product, dependencies=[Depends(security.get_current_active_admin)])
def delete_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
):
    """
    Delete a product.
    """
    product = db.query(models.Product).options(
        joinedload(models.Product.licenses)
    ).filter(models.Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    deleted_product = crud.product.remove(db=db, id=product_id)
    return product