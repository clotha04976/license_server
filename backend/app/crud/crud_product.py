from .base import CRUDBase
from ..models.product import Product
from ..schemas import ProductCreate, ProductUpdate

class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    # You can add custom CRUD methods here if needed
    pass

product = CRUDProduct(Product)