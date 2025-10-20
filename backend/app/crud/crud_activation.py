from sqlalchemy.orm import Session
from typing import List

from .base import CRUDBase
from ..models.activation import Activation
from ..schemas import ActivationCreate

class CRUDActivation(CRUDBase[Activation, ActivationCreate, ActivationCreate]):
    def get_activations_by_license_id(self, db: Session, *, license_id: int) -> List[Activation]:
        return db.query(self.model).filter(self.model.license_id == license_id, self.model.status == 'active').all()
    
    def count_active_activations_by_license_id(self, db: Session, *, license_id: int) -> int:
        """計算指定授權的 active 啟用記錄數量"""
        return db.query(self.model).filter(
            self.model.license_id == license_id, 
            self.model.status == 'active'
        ).count()

activation = CRUDActivation(Activation)