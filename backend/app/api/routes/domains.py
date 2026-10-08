from fastapi import APIRouter

from ...domain_config import DOMAIN_NAMES
from ...schemas.domain import Domain


router = APIRouter(prefix="/api", tags=["domains"])


@router.get("/domains", response_model=list[Domain])
def list_domains() -> list[Domain]:
    return [Domain(name=name) for name in DOMAIN_NAMES]