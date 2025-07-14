from fastapi import APIRouter
from app.core.monitoring import get_monitoring_dashboard

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/dashboard")
def monitoring_dashboard():
    return get_monitoring_dashboard() 