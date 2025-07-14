from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from uuid import UUID
from app.api.deps import SessionDep, CurrentUser
from app import crud

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/project/{project_id}/progress")
def project_progress(project_id: UUID, session: SessionDep, current_user: CurrentUser):
    if not crud.user_has_project_access(session, current_user.id, project_id):
        raise HTTPException(status_code=403, detail="No access to this project")
    # Use cached project metadata
    project = crud.get_project_cached(session, str(project_id))
    return crud.get_project_progress(session, project_id)

@router.get("/team/{team_id}/productivity")
def team_productivity(team_id: UUID, session: SessionDep, current_user: CurrentUser):
    from app.models import TeamMember
    member = session.exec(
        TeamMember.__table__.select().where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        )
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    # Use cached analytics
    analytics = crud.get_dashboard_analytics_cached(session, str(team_id))
    return analytics["progress"]

@router.get("/team/{team_id}/task-stats")
def task_completion_stats(team_id: UUID, session: SessionDep, current_user: CurrentUser):
    from app.models import TeamMember
    member = session.exec(
        TeamMember.__table__.select().where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        )
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    analytics = crud.get_dashboard_analytics_cached(session, str(team_id))
    return analytics["stats"]

@router.get("/team/{team_id}/deadlines")
def deadlines(team_id: UUID, session: SessionDep, current_user: CurrentUser):
    from app.models import TeamMember
    member = session.exec(
        TeamMember.__table__.select().where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        )
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    analytics = crud.get_dashboard_analytics_cached(session, str(team_id))
    return analytics["deadlines"]

@router.get("/team/{team_id}/activity")
def activity_timeline(team_id: UUID, session: SessionDep, current_user: CurrentUser, limit: int = 50):
    from app.models import TeamMember
    member = session.exec(
        TeamMember.__table__.select().where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        )
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    analytics = crud.get_dashboard_analytics_cached(session, str(team_id))
    return analytics["activity"]

@router.get("/cache/metrics")
def cache_metrics():
    return crud.get_cache_metrics() 