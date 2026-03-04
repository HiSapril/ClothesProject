from fastapi import APIRouter
from app.domain.fashion_taxonomy import FashionCategory, ClassificationStatus
from app.db.models import OccasionEnum, UserRole
from app.schemas import schemas

router = APIRouter()

@router.get("/enums", response_model=schemas.EnumExposureResponse, tags=["Metadata"])
def get_enums():
    """
    Expose all system enums to help frontend developers 
    understand allowed values and avoid magic strings.
    """
    return {
        "fashion_categories": [e.value for e in FashionCategory],
        "classification_statuses": [e.value for e in ClassificationStatus],
        "occasions": [e.value for e in OccasionEnum],
        "user_roles": [e.value for e in UserRole]
    }
