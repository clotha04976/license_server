from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .... import crud, schemas
from ....core.dependencies import get_db
from ....core import security

router = APIRouter()

@router.post("/", response_model=schemas.Feature, dependencies=[Depends(security.get_current_active_admin)])
def create_feature(
    *,
    db: Session = Depends(get_db),
    feature_in: schemas.FeatureCreate,
):
    """
    Create new feature.
    """
    feature = crud.feature.create(db=db, obj_in=feature_in)
    return feature

@router.get("/", response_model=List[schemas.Feature], dependencies=[Depends(security.get_current_active_admin)])
def read_features(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve features.
    """
    features = crud.feature.get_multi(db, skip=skip, limit=limit)
    return features

@router.put("/{feature_id}", response_model=schemas.Feature, dependencies=[Depends(security.get_current_active_admin)])
def update_feature(
    *,
    db: Session = Depends(get_db),
    feature_id: int,
    feature_in: schemas.FeatureUpdate,
):
    """
    Update a feature.
    """
    feature = crud.feature.get(db=db, id=feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    feature = crud.feature.update(db=db, db_obj=feature, obj_in=feature_in)
    return feature

@router.delete("/{feature_id}", response_model=schemas.Feature, dependencies=[Depends(security.get_current_active_admin)])
def delete_feature(
    *,
    db: Session = Depends(get_db),
    feature_id: int,
):
    """
    Delete a feature.
    """
    feature = crud.feature.get(db=db, id=feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    feature = crud.feature.remove(db=db, id=feature_id)
    return feature