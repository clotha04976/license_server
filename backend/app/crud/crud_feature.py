from .base import CRUDBase
from ..models.feature import Feature
from ..schemas import FeatureCreate, FeatureUpdate

class CRUDFeature(CRUDBase[Feature, FeatureCreate, FeatureUpdate]):
    # You can add custom CRUD methods here if needed
    pass

feature = CRUDFeature(Feature)