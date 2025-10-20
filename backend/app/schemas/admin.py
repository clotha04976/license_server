from pydantic import BaseModel, EmailStr
from typing import Optional

# Base properties
class AdminBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True

# Properties to receive on creation
class AdminCreate(AdminBase):
    password: str

# Properties to receive on update
class AdminUpdate(AdminBase):
    password: Optional[str] = None

# Properties shared by models stored in DB
class AdminInDBBase(AdminBase):
    id: int

    class Config:
        from_attributes = True

# Properties to return to client
class Admin(AdminInDBBase):
    pass

# Properties stored in DB
class AdminInDB(AdminInDBBase):
    hashed_password: str