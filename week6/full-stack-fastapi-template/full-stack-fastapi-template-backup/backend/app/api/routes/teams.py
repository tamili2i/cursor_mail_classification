from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from uuid import UUID

from app.api.deps import SessionDep, CurrentUser, require_team_role
from app.models import Team, TeamCreate, TeamUpdate, TeamRead, TeamMember, TeamMemberCreate, TeamMemberRead, TeamRole, UserProfile, UserProfileCreate
from app import crud

router = APIRouter(prefix="/teams", tags=["teams"])

@router.post("/", response_model=TeamRead)
def create_team(
    *, session: SessionDep, current_user: CurrentUser, team_in: TeamCreate
):
    team = crud.create_team(session=session, team_create=team_in, owner_id=current_user.id)
    crud.add_team_member(session, team_id=team.id, user_id=current_user.id, role=TeamRole.admin)
    crud.log_activity(session, user_id=current_user.id, action="create_team", entity_type="team", entity_id=team.id)
    crud.invalidate_team_cache(str(team.id))
    crud.invalidate_team_members_cache(str(team.id))
    return team

@router.get("/", response_model=list[TeamRead])
def list_teams(session: SessionDep, current_user: CurrentUser):
    teams = crud.list_teams(session, user_id=current_user.id)
    return [crud.get_team_cached(session, str(t.id)) or t for t in teams]

@router.get("/{team_id}", response_model=TeamRead)
def get_team(team_id: UUID, session: SessionDep, current_user: CurrentUser):
    team = crud.get_team_cached(session, str(team_id))
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.patch("/{team_id}", response_model=TeamRead)
def update_team(
    team_id: UUID,
    team_in: TeamUpdate,
    session: SessionDep,
    current_user: CurrentUser,
    member: TeamMember = Depends(require_team_role(TeamRole.admin)),
):
    team = crud.get_team(session, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    team = crud.update_team(session, db_team=team, team_update=team_in)
    crud.log_activity(session, user_id=current_user.id, action="update_team", entity_type="team", entity_id=team.id)
    crud.invalidate_team_cache(str(team_id))
    return team

@router.delete("/{team_id}")
def delete_team(
    team_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    member: TeamMember = Depends(require_team_role(TeamRole.admin)),
):
    team = crud.get_team(session, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    crud.delete_team(session, db_team=team)
    crud.log_activity(session, user_id=current_user.id, action="delete_team", entity_type="team", entity_id=team.id)
    crud.invalidate_team_cache(str(team_id))
    crud.invalidate_team_members_cache(str(team_id))
    return {"message": "Team deleted"}

@router.get("/{team_id}/members", response_model=list[TeamMemberRead])
def list_team_members(
    team_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    member: TeamMember = Depends(require_team_role(TeamRole.viewer)),
):
    members = crud.get_team_members_cached(session, str(team_id))
    return members

@router.post("/{team_id}/invite")
def invite_member(
    team_id: UUID,
    user_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    member: TeamMember = Depends(require_team_role(TeamRole.admin)),
):
    invited_member = crud.add_team_member(session, team_id=team_id, user_id=user_id, role=TeamRole.member, invited=True)
    crud.log_activity(session, user_id=current_user.id, action="invite_member", entity_type="team_member", entity_id=invited_member.id, team_id=team_id)
    crud.invalidate_team_members_cache(str(team_id))
    return {"message": "Invitation sent"}

@router.post("/{team_id}/members/{user_id}/role")
def update_member_role(
    team_id: UUID,
    user_id: UUID,
    role: TeamRole,
    session: SessionDep,
    current_user: CurrentUser,
    member: TeamMember = Depends(require_team_role(TeamRole.admin)),
):
    team_member = crud.get_team_member(session, team_id, user_id)
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member not found")
    crud.update_team_member(session, team_member, role=role)
    crud.log_activity(session, user_id=current_user.id, action="update_member_role", entity_type="team_member", entity_id=team_member.id, team_id=team_id, data={"role": role})
    crud.invalidate_team_members_cache(str(team_id))
    return {"message": "Role updated"}

@router.delete("/{team_id}/members/{user_id}")
def remove_member(
    team_id: UUID,
    user_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    member: TeamMember = Depends(require_team_role(TeamRole.admin)),
):
    team_member = crud.get_team_member(session, team_id, user_id)
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member not found")
    crud.remove_team_member(session, team_member)
    crud.log_activity(session, user_id=current_user.id, action="remove_member", entity_type="team_member", entity_id=team_member.id, team_id=team_id)
    crud.invalidate_team_members_cache(str(team_id))
    return {"message": "Member removed"} 