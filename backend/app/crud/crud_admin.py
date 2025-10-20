from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from ..models.admin import Admin
from ..schemas.admin import AdminCreate, AdminUpdate
from ..core.utils import get_password_hash

class CRUDAdmin:
    def get(self, db: Session, id: Any) -> Optional[Admin]:
        return db.query(Admin).filter(Admin.id == id).first()

    def get_by_username(self, db: Session, username: str) -> Optional[Admin]:
        return db.query(Admin).filter(Admin.username == username).first()

    def create(self, db: Session, obj_in: AdminCreate) -> Admin:
        create_data = obj_in.dict(exclude_unset=True)
        hashed_password = get_password_hash(obj_in.password)
        db_obj = Admin(**create_data, hashed_password=hashed_password)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        db_obj: Admin,
        obj_in: Union[AdminUpdate, Dict[str, Any]],
    ) -> Admin:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        if "password" in update_data:
            hashed_password = get_password_hash(update_data.pop("password"))
            update_data["hashed_password"] = hashed_password

        for field in update_data:
            if field in ["username", "is_active", "is_superuser"]:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Admin:
        obj = db.query(Admin).get(id)
        db.delete(obj)
        db.commit()
        return obj

admin = CRUDAdmin()