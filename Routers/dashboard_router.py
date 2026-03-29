from fastapi import APIRouter, Request, Query
from Controller.dashboard_controller import get_dashboard_stats, get_recent_activity

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def fetch_dashboard_stats(request: Request):
    user_id = request.state.user_id
    return await get_dashboard_stats(user_id)


@router.get("/recent-activity")
async def fetch_recent_activity(
    request: Request,
    limit: int = Query(10, ge=1, le=100)
):
    user_id = request.state.user_id
    return await get_recent_activity(user_id, limit)