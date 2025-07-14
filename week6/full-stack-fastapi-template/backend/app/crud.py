import uuid
from typing import Any
from datetime import datetime, timezone

from sqlmodel import Session, select
from sqlmodel import func

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate, Team, TeamCreate, TeamUpdate, TeamMember, TeamMemberCreate, UserProfile, UserProfileCreate, ActivityLog, Project, ProjectCreate, ProjectUpdate, Task, TaskCreate, TaskUpdate, TaskDependency, TaskAttachment, TaskAttachmentBase, TaskComment, TaskCommentBase, TaskPriority
from app.core.redis import redis_set, redis_get, redis_delete
import json

SESSION_TTL = 60 * 60 * 24  # 24 hours

def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

# TEAM CRUD

def create_team(*, session: Session, team_create: TeamCreate, owner_id: uuid.UUID) -> Team:
    db_team = Team.model_validate(team_create, update={"owner_id": owner_id})
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team

def get_team(session: Session, team_id: uuid.UUID) -> Team | None:
    return session.get(Team, team_id)

def update_team(session: Session, db_team: Team, team_update: TeamUpdate) -> Team:
    update_data = team_update.model_dump(exclude_unset=True)
    db_team.sqlmodel_update(update_data)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team

def delete_team(session: Session, db_team: Team) -> None:
    session.delete(db_team)
    session.commit()

def list_teams(session: Session, user_id: uuid.UUID) -> list[Team]:
    statement = select(Team).join(TeamMember).where(TeamMember.user_id == user_id)
    return session.exec(statement).all()

# TEAM MEMBER CRUD

def add_team_member(session: Session, team_id: uuid.UUID, user_id: uuid.UUID, role: str = "member", invited: bool = False) -> TeamMember:
    member = TeamMember(team_id=team_id, user_id=user_id, role=role, invited=invited)
    session.add(member)
    session.commit()
    session.refresh(member)
    return member

def get_team_member(session: Session, team_id: uuid.UUID, user_id: uuid.UUID) -> TeamMember | None:
    statement = select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
    return session.exec(statement).first()

def update_team_member(session: Session, member: TeamMember, role: str | None = None, invited: bool | None = None) -> TeamMember:
    if role:
        member.role = role
    if invited is not None:
        member.invited = invited
    session.add(member)
    session.commit()
    session.refresh(member)
    return member

def remove_team_member(session: Session, member: TeamMember) -> None:
    session.delete(member)
    session.commit()

def list_team_members(session: Session, team_id: uuid.UUID) -> list[TeamMember]:
    statement = select(TeamMember).where(TeamMember.team_id == team_id)
    return session.exec(statement).all()

# USER PROFILE CRUD

def create_user_profile(session: Session, user_id: uuid.UUID, profile_create: UserProfileCreate) -> UserProfile:
    profile = UserProfile.model_validate(profile_create, update={"user_id": user_id})
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile

def get_user_profile(session: Session, user_id: uuid.UUID) -> UserProfile | None:
    statement = select(UserProfile).where(UserProfile.user_id == user_id)
    return session.exec(statement).first()

def update_user_profile(session: Session, profile: UserProfile, update_data: dict) -> UserProfile:
    profile.sqlmodel_update(update_data)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile

# ACTIVITY LOG

def log_activity(session: Session, user_id: uuid.UUID, action: str, entity_type: str, entity_id: uuid.UUID | None = None, team_id: uuid.UUID | None = None, data: dict | None = None) -> ActivityLog:
    log = ActivityLog(user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id, team_id=team_id, data=data)
    session.add(log)
    session.commit()
    session.refresh(log)
    return log

def list_activity_logs(session: Session, user_id: uuid.UUID, team_id: uuid.UUID | None = None) -> list[ActivityLog]:
    statement = select(ActivityLog).where(ActivityLog.user_id == user_id)
    if team_id:
        statement = statement.where(ActivityLog.team_id == team_id)
    return session.exec(statement).all()

# PROJECT CRUD

def create_project(session: Session, project_create: ProjectCreate) -> Project:
    db_project = Project.model_validate(project_create)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

def get_project(session: Session, project_id: uuid.UUID) -> Project | None:
    return session.get(Project, project_id)

def update_project(session: Session, db_project: Project, project_update: ProjectUpdate) -> Project:
    update_data = project_update.model_dump(exclude_unset=True)
    db_project.sqlmodel_update(update_data)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

def delete_project(session: Session, db_project: Project) -> None:
    session.delete(db_project)
    session.commit()

def list_projects(session: Session, team_id: uuid.UUID) -> list[Project]:
    statement = select(Project).where(Project.team_id == team_id)
    return session.exec(statement).all()

# TASK CRUD

def create_task(session: Session, task_create: TaskCreate) -> Task:
    db_task = Task.model_validate(task_create)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

def get_task(session: Session, task_id: uuid.UUID) -> Task | None:
    return session.get(Task, task_id)

def update_task(session: Session, db_task: Task, task_update: TaskUpdate) -> Task:
    update_data = task_update.model_dump(exclude_unset=True)
    db_task.sqlmodel_update(update_data)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

def delete_task(session: Session, db_task: Task) -> None:
    session.delete(db_task)
    session.commit()

def list_tasks(session: Session, project_id: uuid.UUID) -> list[Task]:
    statement = select(Task).where(Task.project_id == project_id)
    return session.exec(statement).all()

# --- PAGINATION FOR TASK LISTS ---
def list_tasks_paginated(session, project_id, limit=50, offset=0):
    statement = select(Task).where(Task.project_id == project_id).offset(offset).limit(limit)
    tasks = session.exec(statement).all()
    total = session.exec(select(func.count()).where(Task.project_id == project_id)).one()
    return tasks, total

def get_task_list_cached_paginated(session, project_id: str, limit=50, offset=0):
    cache_key = f"task:list:{project_id}:{limit}:{offset}"
    cached = redis_get(cache_key)
    if cached:
        return cached
    tasks, total = list_tasks_paginated(session, project_id, limit, offset)
    if tasks:
        redis_set(cache_key, {"tasks": [t.model_dump() for t in tasks], "total": total}, ex=TASK_TTL)
    return {"tasks": tasks, "total": total}

# TASK DEPENDENCY CRUD

def add_task_dependency(session: Session, task_id: uuid.UUID, depends_on_id: uuid.UUID) -> TaskDependency:
    dep = TaskDependency(task_id=task_id, depends_on_id=depends_on_id)
    session.add(dep)
    session.commit()
    session.refresh(dep)
    return dep

def remove_task_dependency(session: Session, dep: TaskDependency) -> None:
    session.delete(dep)
    session.commit()

def list_task_dependencies(session: Session, task_id: uuid.UUID) -> list[TaskDependency]:
    statement = select(TaskDependency).where(TaskDependency.task_id == task_id)
    return session.exec(statement).all()

# TASK ATTACHMENT CRUD

def add_task_attachment(session: Session, task_id: uuid.UUID, attachment_in: TaskAttachmentBase) -> TaskAttachment:
    attachment = TaskAttachment.model_validate(attachment_in, update={"task_id": task_id})
    session.add(attachment)
    session.commit()
    session.refresh(attachment)
    return attachment

def list_task_attachments(session: Session, task_id: uuid.UUID) -> list[TaskAttachment]:
    statement = select(TaskAttachment).where(TaskAttachment.task_id == task_id)
    return session.exec(statement).all()

# TASK COMMENT CRUD

def add_task_comment(session: Session, task_id: uuid.UUID, comment_in: TaskCommentBase) -> TaskComment:
    comment = TaskComment.model_validate(comment_in, update={"task_id": task_id})
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment

def list_task_comments(session: Session, task_id: uuid.UUID) -> list[TaskComment]:
    statement = select(TaskComment).where(TaskComment.task_id == task_id)
    return session.exec(statement).all()

# PROJECT PERMISSION CHECK

def user_has_project_access(session: Session, user_id: uuid.UUID, project_id: uuid.UUID) -> bool:
    project = get_project(session, project_id)
    if not project:
        return False
    from app.models import TeamMember
    statement = select(TeamMember).where(TeamMember.team_id == project.team_id, TeamMember.user_id == user_id)
    return session.exec(statement).first() is not None

# DASHBOARD ANALYTICS

def get_project_progress(session: Session, project_id: uuid.UUID):
    from app.models import Task
    total = session.exec(select(Task).where(Task.project_id == project_id)).count()
    completed = session.exec(select(Task).where(Task.project_id == project_id, Task.status == "completed")).count()
    progress = (completed / total) * 100 if total else 0
    return {"total": total, "completed": completed, "progress": progress}

def get_team_productivity(session: Session, team_id: uuid.UUID):
    from app.models import Project, Task
    project_ids = [p.id for p in session.exec(select(Project.id).where(Project.team_id == team_id)).all()]
    if not project_ids:
        return {"tasks_completed": 0, "tasks_created": 0, "completion_rate": 0}
    total = session.exec(select(Task).where(Task.project_id.in_(project_ids))).count()
    completed = session.exec(select(Task).where(Task.project_id.in_(project_ids), Task.status == "completed")).count()
    completion_rate = (completed / total) * 100 if total else 0
    return {"tasks_completed": completed, "tasks_created": total, "completion_rate": completion_rate}

def get_task_completion_stats(session: Session, team_id: uuid.UUID):
    from app.models import Project, Task
    project_ids = [p.id for p in session.exec(select(Project.id).where(Project.team_id == team_id)).all()]
    if not project_ids:
        return {"open": 0, "in_progress": 0, "completed": 0}
    open_ = session.exec(select(Task).where(Task.project_id.in_(project_ids), Task.status == "open")).count()
    in_progress = session.exec(select(Task).where(Task.project_id.in_(project_ids), Task.status == "in_progress")).count()
    completed = session.exec(select(Task).where(Task.project_id.in_(project_ids), Task.status == "completed")).count()
    return {"open": open_, "in_progress": in_progress, "completed": completed}

def get_upcoming_and_overdue_tasks(session: Session, team_id: uuid.UUID):
    from app.models import Project, Task
    now = datetime.now(timezone.utc).timestamp()
    project_ids = [p.id for p in session.exec(select(Project.id).where(Project.team_id == team_id)).all()]
    if not project_ids:
        return {"upcoming": [], "overdue": []}
    upcoming = session.exec(
        select(Task).where(Task.project_id.in_(project_ids), Task.due_date != None, Task.due_date > now, Task.status != "completed")
    ).all()
    overdue = session.exec(
        select(Task).where(Task.project_id.in_(project_ids), Task.due_date != None, Task.due_date <= now, Task.status != "completed")
    ).all()
    return {"upcoming": upcoming, "overdue": overdue}

def get_team_activity_timeline(session: Session, team_id: uuid.UUID, limit: int = 50):
    from app.models import ActivityLog
    logs = session.exec(
        select(ActivityLog).where(ActivityLog.team_id == team_id).order_by(ActivityLog.timestamp.desc()).limit(limit)
    ).all()
    return logs

# USER SESSION CACHING

def cache_user_session(user_id: str, token: str, user_data: dict):
    redis_set(f"session:{user_id}", {"token": token, "user": user_data}, ex=SESSION_TTL)
    redis_set(f"token:{token}", user_id, ex=SESSION_TTL)

def get_user_session_by_token(token: str):
    user_id = redis_get(f"token:{token}")
    if not user_id:
        return None
    return redis_get(f"session:{user_id}")

def delete_user_session(user_id: str, token: str = None):
    redis_delete(f"session:{user_id}")
    if token:
        redis_delete(f"token:{token}")

# --- PROJECT METADATA CACHING ---
PROJECT_TTL = 60 * 10  # 10 minutes
PROJECT_CACHE_KEY = lambda project_id: f"project:meta:{project_id}"

project_cache_hits = 0
project_cache_misses = 0


def get_project_cached(session: Session, project_id: str):
    global project_cache_hits, project_cache_misses
    cached = redis_get(PROJECT_CACHE_KEY(project_id))
    if cached:
        project_cache_hits += 1
        return cached
    project = get_project(session, project_id)
    if project:
        redis_set(PROJECT_CACHE_KEY(project_id), project.model_dump(), ex=PROJECT_TTL)
        project_cache_misses += 1
    return project

def invalidate_project_cache(project_id: str):
    redis_delete(PROJECT_CACHE_KEY(project_id))

# --- DASHBOARD ANALYTICS CACHING ---
DASHBOARD_TTL = 60 * 5  # 5 minutes
DASHBOARD_CACHE_KEY = lambda team_id: f"dashboard:analytics:{team_id}"

def get_dashboard_analytics_cached(session: Session, team_id: str):
    cached = redis_get(DASHBOARD_CACHE_KEY(team_id))
    if cached:
        return cached
    analytics = {
        "progress": get_team_productivity(session, team_id),
        "stats": get_task_completion_stats(session, team_id),
        "deadlines": get_upcoming_and_overdue_tasks(session, team_id),
        "activity": get_team_activity_timeline(session, team_id, limit=20),
    }
    redis_set(DASHBOARD_CACHE_KEY(team_id), analytics, ex=DASHBOARD_TTL)
    return analytics

def invalidate_dashboard_cache(team_id: str):
    redis_delete(DASHBOARD_CACHE_KEY(team_id))

# --- TASK DATA CACHING ---
TASK_TTL = 60 * 10
TASK_CACHE_KEY = lambda task_id: f"task:data:{task_id}"
TASK_LIST_CACHE_KEY = lambda project_id: f"task:list:{project_id}"
task_cache_hits = 0
task_cache_misses = 0

def get_task_cached(session: Session, task_id: str):
    global task_cache_hits, task_cache_misses
    cached = redis_get(TASK_CACHE_KEY(task_id))
    if cached:
        task_cache_hits += 1
        return cached
    task = get_task(session, task_id)
    if task:
        redis_set(TASK_CACHE_KEY(task_id), task.model_dump(), ex=TASK_TTL)
        task_cache_misses += 1
    return task

def invalidate_task_cache(task_id: str):
    redis_delete(TASK_CACHE_KEY(task_id))

def get_task_list_cached(session: Session, project_id: str):
    cached = redis_get(TASK_LIST_CACHE_KEY(project_id))
    if cached:
        return cached
    tasks = list_tasks(session, project_id)
    if tasks:
        redis_set(TASK_LIST_CACHE_KEY(project_id), [t.model_dump() for t in tasks], ex=TASK_TTL)
    return tasks

def invalidate_task_list_cache(project_id: str):
    redis_delete(TASK_LIST_CACHE_KEY(project_id))

# --- TEAM CACHING ---
TEAM_TTL = 60 * 10
TEAM_CACHE_KEY = lambda team_id: f"team:meta:{team_id}"
TEAM_MEMBERS_CACHE_KEY = lambda team_id: f"team:members:{team_id}"
team_cache_hits = 0
team_cache_misses = 0

def get_team_cached(session: Session, team_id: str):
    global team_cache_hits, team_cache_misses
    cached = redis_get(TEAM_CACHE_KEY(team_id))
    if cached:
        team_cache_hits += 1
        return cached
    team = get_team(session, team_id)
    if team:
        redis_set(TEAM_CACHE_KEY(team_id), team.model_dump(), ex=TEAM_TTL)
        team_cache_misses += 1
    return team

def invalidate_team_cache(team_id: str):
    redis_delete(TEAM_CACHE_KEY(team_id))

def get_team_members_cached(session: Session, team_id: str):
    cached = redis_get(TEAM_MEMBERS_CACHE_KEY(team_id))
    if cached:
        return cached
    members = list_team_members(session, team_id)
    if members:
        redis_set(TEAM_MEMBERS_CACHE_KEY(team_id), [m.model_dump() for m in members], ex=TEAM_TTL)
    return members

def invalidate_team_members_cache(team_id: str):
    redis_delete(TEAM_MEMBERS_CACHE_KEY(team_id))

# --- USER CACHING ---
USER_TTL = 60 * 10
USER_CACHE_KEY = lambda user_id: f"user:profile:{user_id}"
USER_LIST_CACHE_KEY = "user:list"
user_cache_hits = 0
user_cache_misses = 0

def get_user_cached(session: Session, user_id: str):
    global user_cache_hits, user_cache_misses
    cached = redis_get(USER_CACHE_KEY(user_id))
    if cached:
        user_cache_hits += 1
        return cached
    user = session.get(User, user_id)
    if user:
        redis_set(USER_CACHE_KEY(user_id), user.model_dump(), ex=USER_TTL)
        user_cache_misses += 1
    return user

def invalidate_user_cache(user_id: str):
    redis_delete(USER_CACHE_KEY(user_id))

def get_user_list_cached(session: Session):
    cached = redis_get(USER_LIST_CACHE_KEY)
    if cached:
        return cached
    from sqlmodel import select
    users = session.exec(select(User)).all()
    if users:
        redis_set(USER_LIST_CACHE_KEY, [u.model_dump() for u in users], ex=USER_TTL)
    return users

def invalidate_user_list_cache():
    redis_delete(USER_LIST_CACHE_KEY)

# --- NOTIFICATION CACHING ---
NOTIF_TTL = 60 * 5
NOTIF_CACHE_KEY = lambda user_id: f"notif:list:{user_id}"
notif_cache_hits = 0
notif_cache_misses = 0

def get_notifications_cached(session: Session, user_id: str):
    global notif_cache_hits, notif_cache_misses
    cached = redis_get(NOTIF_CACHE_KEY(user_id))
    if cached:
        notif_cache_hits += 1
        return cached
    # Assume notifications are in ActivityLog or Notification model
    from app.models import Notification
    from sqlmodel import select
    notifs = session.exec(select(Notification).where(Notification.user_id == user_id)).all()
    if notifs:
        redis_set(NOTIF_CACHE_KEY(user_id), [n.model_dump() for n in notifs], ex=NOTIF_TTL)
        notif_cache_misses += 1
    return notifs

def invalidate_notifications_cache(user_id: str):
    redis_delete(NOTIF_CACHE_KEY(user_id))

# --- ACTIVITY LOG CACHING ---
ACTIVITY_TTL = 60 * 5
ACTIVITY_CACHE_KEY = lambda team_id: f"activity:log:{team_id}"
activity_cache_hits = 0
activity_cache_misses = 0

def get_activity_log_cached(session: Session, team_id: str, limit: int = 50):
    global activity_cache_hits, activity_cache_misses
    cached = redis_get(ACTIVITY_CACHE_KEY(team_id))
    if cached:
        activity_cache_hits += 1
        return cached[:limit]
    logs = get_team_activity_timeline(session, team_id, limit=limit)
    if logs:
        redis_set(ACTIVITY_CACHE_KEY(team_id), [l.model_dump() for l in logs], ex=ACTIVITY_TTL)
        activity_cache_misses += 1
    return logs

def invalidate_activity_log_cache(team_id: str):
    redis_delete(ACTIVITY_CACHE_KEY(team_id))

# --- SMART CACHE INVALIDATION HOOKS ---
def on_project_update(project_id: str, team_id: str = None):
    invalidate_project_cache(project_id)
    if team_id:
        invalidate_dashboard_cache(team_id)
    invalidate_task_list_cache(project_id)

def on_task_update(task_id: str, project_id: str, team_id: str = None):
    invalidate_task_cache(task_id)
    invalidate_task_list_cache(project_id)
    if team_id:
        invalidate_dashboard_cache(team_id)

# --- CACHE WARMING FOR POPULAR PROJECTS ---
def warm_project_cache(session: Session, project_ids: list):
    for pid in project_ids:
        get_project_cached(session, pid)
        get_task_list_cached(session, pid)

# --- METRICS EXTENSION ---
def get_cache_metrics():
    base = {
        "project_cache_hits": project_cache_hits,
        "project_cache_misses": project_cache_misses,
        "task_cache_hits": task_cache_hits,
        "task_cache_misses": task_cache_misses,
    }
    base.update({
        "team_cache_hits": team_cache_hits,
        "team_cache_misses": team_cache_misses,
        "user_cache_hits": user_cache_hits,
        "user_cache_misses": user_cache_misses,
        "notif_cache_hits": notif_cache_hits,
        "notif_cache_misses": notif_cache_misses,
        "activity_cache_hits": activity_cache_hits,
        "activity_cache_misses": activity_cache_misses,
    })
    return base
