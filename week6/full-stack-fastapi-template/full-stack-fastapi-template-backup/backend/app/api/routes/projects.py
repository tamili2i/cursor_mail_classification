from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session
from uuid import UUID
from app.api.deps import SessionDep, CurrentUser, require_project_access
from app.models import (
    Project, ProjectCreate, ProjectUpdate, ProjectRead,
    Task, TaskCreate, TaskUpdate, TaskRead, TaskPriority,
    TaskAttachmentBase, TaskCommentBase
)
from app import crud

router = APIRouter(prefix="/projects", tags=["projects"])

# Project Endpoints
@router.post("/", response_model=ProjectRead)
def create_project(
    *, session: SessionDep, current_user: CurrentUser, project_in: ProjectCreate
):
    # Only team members can create projects
    from app.models import TeamMember
    member = session.exec(
        TeamMember.__table__.select().where(
            TeamMember.team_id == project_in.team_id,
            TeamMember.user_id == current_user.id
        )
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    project = crud.create_project(session, project_in)
    # Cache warm for new project
    crud.warm_project_cache(session, [str(project.id)])
    return project

@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: UUID, session: SessionDep, current_user: CurrentUser, 
                _: None = Depends(require_project_access())):
    project = crud.get_project_cached(session, str(project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: UUID, project_in: ProjectUpdate, session: SessionDep, current_user: CurrentUser, 
                  _: None = Depends(require_project_access())):
    project = crud.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project = crud.update_project(session, project, project_in)
    crud.on_project_update(str(project_id), str(project.team_id))
    return project

@router.delete("/{project_id}")
def delete_project(project_id: UUID, session: SessionDep, current_user: CurrentUser, 
                  _: None = Depends(require_project_access())):
    project = crud.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    crud.delete_project(session, project)
    crud.on_project_update(str(project_id), str(project.team_id))
    return {"message": "Project deleted"}

@router.get("/team/{team_id}", response_model=list[ProjectRead])
def list_projects(team_id: UUID, session: SessionDep, current_user: CurrentUser):
    # Only team members can list projects
    from app.models import TeamMember
    member = session.exec(
        TeamMember.__table__.select().where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        )
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    # Use cached project metadata for each project
    projects = crud.list_projects(session, team_id)
    return [crud.get_project_cached(session, str(p.id)) or p for p in projects]

# Task Endpoints
@router.post("/{project_id}/tasks", response_model=TaskRead)
def create_task(project_id: UUID, task_in: TaskCreate, session: SessionDep, current_user: CurrentUser, 
               _: None = Depends(require_project_access())):
    if task_in.project_id != project_id:
        raise HTTPException(status_code=400, detail="Project ID mismatch")
    task = crud.create_task(session, task_in)
    crud.on_task_update(str(task.id), str(project_id))
    return task

@router.get("/{project_id}/tasks", response_model=dict)
def list_tasks(project_id: UUID, session: SessionDep, current_user: CurrentUser, 
              _: None = Depends(require_project_access()), limit: int = 50, offset: int = 0):
    # Use cached paginated task list
    result = crud.get_task_list_cached_paginated(session, str(project_id), limit, offset)
    return result

@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: UUID, session: SessionDep, current_user: CurrentUser):
    task = crud.get_task_cached(session, str(task_id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Permission: must have access to project
    if not crud.user_has_project_access(session, current_user.id, task["project_id"] if isinstance(task, dict) else task.project_id):
        raise HTTPException(status_code=403, detail="No access to this project")
    return task

@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: UUID, task_in: TaskUpdate, session: SessionDep, current_user: CurrentUser):
    task = crud.get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not crud.user_has_project_access(session, current_user.id, task.project_id):
        raise HTTPException(status_code=403, detail="No access to this project")
    task = crud.update_task(session, task, task_in)
    crud.on_task_update(str(task_id), str(task.project_id))
    return task

@router.delete("/tasks/{task_id}")
def delete_task(task_id: UUID, session: SessionDep, current_user: CurrentUser):
    task = crud.get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not crud.user_has_project_access(session, current_user.id, task.project_id):
        raise HTTPException(status_code=403, detail="No access to this project")
    crud.delete_task(session, task)
    crud.on_task_update(str(task_id), str(task.project_id))
    return {"message": "Task deleted"}

# Task Dependencies
@router.post("/tasks/{task_id}/dependencies")
def add_dependency(task_id: UUID, depends_on_id: UUID, session: SessionDep, current_user: CurrentUser):
    task = crud.get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not crud.user_has_project_access(session, current_user.id, task.project_id):
        raise HTTPException(status_code=403, detail="No access to this project")
    dep = crud.add_task_dependency(session, task_id, depends_on_id)
    return {"message": "Dependency added", "id": dep.id}

@router.get("/tasks/{task_id}/dependencies")
def list_dependencies(task_id: UUID, session: SessionDep, current_user: CurrentUser):
    task = crud.get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not crud.user_has_project_access(session, current_user.id, task.project_id):
        raise HTTPException(status_code=403, detail="No access to this project")
    return crud.list_task_dependencies(session, task_id)

# Task Attachments
@router.post("/tasks/{task_id}/attachments")
def add_attachment(task_id: UUID, file_url: str, uploaded_by: UUID, session: SessionDep, current_user: CurrentUser):
    task = crud.get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not crud.user_has_project_access(session, current_user.id, task.project_id):
        raise HTTPException(status_code=403, detail="No access to this project")
    attachment_in = TaskAttachmentBase(file_url=file_url, uploaded_by=uploaded_by)
    attachment = crud.add_task_attachment(session, task_id, attachment_in)
    return {"message": "Attachment added", "id": attachment.id}

@router.get("/tasks/{task_id}/attachments")
def list_attachments(task_id: UUID, session: SessionDep, current_user: CurrentUser):
    task = crud.get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not crud.user_has_project_access(session, current_user.id, task.project_id):
        raise HTTPException(status_code=403, detail="No access to this project")
    return crud.list_task_attachments(session, task_id)

# Task Comments
@router.post("/tasks/{task_id}/comments")
def add_comment(task_id: UUID, content: str, user_id: UUID, session: SessionDep, current_user: CurrentUser):
    task = crud.get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not crud.user_has_project_access(session, current_user.id, task.project_id):
        raise HTTPException(status_code=403, detail="No access to this project")
    comment_in = TaskCommentBase(content=content, user_id=user_id)
    comment = crud.add_task_comment(session, task_id, comment_in)
    return {"message": "Comment added", "id": comment.id}

@router.get("/tasks/{task_id}/comments")
def list_comments(task_id: UUID, session: SessionDep, current_user: CurrentUser):
    task = crud.get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not crud.user_has_project_access(session, current_user.id, task.project_id):
        raise HTTPException(status_code=403, detail="No access to this project")
    return crud.list_task_comments(session, task_id) 