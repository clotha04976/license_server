from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- Base Schemas ---

class FeatureBase(BaseModel):
    name: str
    description: Optional[str] = None

class CustomerBase(BaseModel):
    tax_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    version: Optional[str] = None

class LicenseBase(BaseModel):
    customer_id: int
    product_id: int
    features: Optional[List[str]] = []
    expires_at: Optional[datetime] = None
    max_activations: int = 1
    status: str = 'pending'
    connection_type: str = 'network'
    notes: Optional[str] = None

class ActivationBase(BaseModel):
    license_id: int
    machine_code: str
    ip_address: Optional[str] = None
    keypro_id: Optional[str] = None
    motherboard_id: Optional[str] = None
    disk_id: Optional[str] = None

# --- Create Schemas ---

class FeatureCreate(FeatureBase):
    pass

class CustomerCreate(CustomerBase):
    pass

class ProductCreate(ProductBase):
    pass

class LicenseCreate(LicenseBase):
    machine_code: Optional[str] = None

class ActivationCreate(ActivationBase):
    pass

# --- Update Schemas ---

class FeatureUpdate(FeatureBase):
    pass

class CustomerUpdate(CustomerBase):
    pass

class ProductUpdate(ProductBase):
    pass

class LicenseUpdate(BaseModel):
    features: Optional[List[str]] = []
    expires_at: Optional[datetime] = None
    max_activations: Optional[int] = None
    status: Optional[str] = None
    connection_type: Optional[str] = None
    notes: Optional[str] = None

# --- Schemas for returning data from DB (with relationships) ---

class Feature(FeatureBase):
    id: int
    class Config:
        from_attributes = True

class Activation(ActivationBase):
    id: int
    status: str
    activated_at: datetime
    class Config:
        from_attributes = True

# To break recursion, we create slimmed-down versions of schemas
# that will be nested inside others.

class LicenseInCustomer(LicenseBase):
    id: int
    serial_number: str
    class Config:
        from_attributes = True

class LicenseInProduct(LicenseBase):
    id: int
    serial_number: str
    class Config:
        from_attributes = True

class CustomerInLicense(CustomerBase):
    id: int
    class Config:
        from_attributes = True

class ProductInLicense(ProductBase):
    id: int
    class Config:
        from_attributes = True

# Now, define the full schemas for top-level responses
class Customer(CustomerBase):
    id: int
    licenses: List[LicenseInCustomer] = []
    class Config:
        from_attributes = True

class Product(ProductBase):
    id: int
    licenses: List[LicenseInProduct] = []
    class Config:
        from_attributes = True

class License(LicenseBase):
    id: int
    serial_number: str
    customer: CustomerInLicense
    product: ProductInLicense
    activations: List[Activation] = []
    class Config:
        from_attributes = True

# --- Search and Pagination Schemas ---

class CustomerSearchParams(BaseModel):
    search: Optional[str] = None
    page: int = 1
    limit: int = 20
    sort_by: Optional[str] = "id"
    sort_order: Optional[str] = "asc"  # "asc" or "desc"

class CustomerSearchResponse(BaseModel):
    items: List[Customer]
    total: int
    page: int
    limit: int
    total_pages: int

class LicenseSearchParams(BaseModel):
    search: Optional[str] = None
    status: Optional[str] = None
    order_by: Optional[str] = "created_at_desc"
    page: int = 1
    limit: int = 20

class LicenseSearchResponse(BaseModel):
    items: List[License]
    total: int
    page: int
    limit: int
    total_pages: int