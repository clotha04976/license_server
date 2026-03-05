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
    app_version: Optional[str] = None

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
    customer_id: Optional[int] = None
    product_id: Optional[int] = None
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

# --- Log Schemas ---

class LogFileInfo(BaseModel):
    filename: str
    file_size: int
    uploaded_at: datetime
    serial_number: str
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_tax_id: Optional[str] = None
    batch_id: Optional[str] = None  # 批次 ID（同一時間上傳的檔案共用同一個批次 ID）
    problem_description: Optional[str] = None  # 問題描述

class LogUploadResponse(BaseModel):
    status: str
    message: str
    uploaded_files: List[str] = []
    failed_files: List[str] = []

class LogListResponse(BaseModel):
    items: List[LogFileInfo]
    total: int
    page: int
    limit: int
    total_pages: int

# --- Training Data Schemas ---

class InvoiceData(BaseModel):
    """單筆發票資料"""
    invoice_number: str  # 發票號碼
    invoice_type: str  # 發票類別
    invoice_date: str  # 發票日期
    seller_id: Optional[str] = ""  # 承賣人統編
    buyer_id: Optional[str] = ""  # 買受人統編
    tax_type: Optional[str] = "1"  # 課稅別
    deductible: Optional[bool] = True  # 是否折抵
    sales_amount: Optional[float] = 0  # 金額
    business_tax: Optional[float] = 0  # 稅額
    is_fix_asset: Optional[bool] = False  # 是否為固定資產
    img_path: str  # 圖片路徑

class TrainingDataUploadRequest(BaseModel):
    """訓練資料上傳請求"""
    serial_number: str
    year: int  # 民國年
    month: int
    invoices: List[InvoiceData]

class TrainingDataUploadResponse(BaseModel):
    """訓練資料上傳回應"""
    status: str
    message: str
    uploaded_images: int = 0
    failed_images: int = 0
    csv_updated: bool = False

class TrainingDataRecord(BaseModel):
    """訓練資料上傳記錄"""
    serial_number: str
    year: int
    month: int
    uploaded_at: datetime
    last_updated: datetime
    invoice_count: int
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_tax_id: Optional[str] = None

class TrainingDataListResponse(BaseModel):
    """訓練資料列表回應"""
    items: List[TrainingDataRecord]
    total: int
    page: int
    limit: int
    total_pages: int