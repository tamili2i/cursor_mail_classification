import uuid

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)

# Team and Role Models
class TeamBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    description: str | None = Field(default=None, max_length=1024)

class TeamCreate(TeamBase):
    pass

class TeamUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1024)

class Team(TeamBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    members: list["TeamMember"] = Relationship(back_populates="team")

class TeamRead(TeamBase):
    id: uuid.UUID
    owner_id: uuid.UUID

# Role Enum
from enum import Enum
class TeamRole(str, Enum):
    admin = "admin"
    member = "member"
    viewer = "viewer"

# Team Member
class TeamMemberBase(SQLModel):
    user_id: uuid.UUID = Field(foreign_key="user.id")
    team_id: uuid.UUID = Field(foreign_key="team.id")
    role: TeamRole = Field(default=TeamRole.member)
    invited: bool = False

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMember(TeamMemberBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user: "User" = Relationship()
    team: Team = Relationship(back_populates="members")

class TeamMemberRead(TeamMemberBase):
    id: uuid.UUID

# User Profile
class UserProfileBase(SQLModel):
    avatar_url: str | None = None
    preferences: dict | None = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfile(UserProfileBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", unique=True)

# Activity Log
class ActivityLogBase(SQLModel):
    user_id: uuid.UUID = Field(foreign_key="user.id")
    team_id: uuid.UUID | None = Field(default=None, foreign_key="team.id")
    action: str
    entity_type: str
    entity_id: uuid.UUID | None = None
    data: dict | None = None

class ActivityLog(ActivityLogBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    timestamp: float = Field(default_factory=lambda: __import__('time').time())

class ProjectBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    description: str | None = Field(default=None, max_length=1024)

class ProjectCreate(ProjectBase):
    team_id: uuid.UUID

class ProjectUpdate(SQLModel):
    name: str | None = None
    description: str | None = None

class Project(ProjectBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    team_id: uuid.UUID = Field(foreign_key="team.id", nullable=False)
    tasks: list["Task"] = Relationship(back_populates="project")

class ProjectRead(ProjectBase):
    id: uuid.UUID
    team_id: uuid.UUID

# Task Priority Enum
class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"

class TaskBase(SQLModel):
    title: str = Field(max_length=255)
    description: str | None = None
    assignee_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    priority: TaskPriority = Field(default=TaskPriority.medium)
    due_date: float | None = None
    status: str = Field(default="open")

class TaskCreate(TaskBase):
    project_id: uuid.UUID
    parent_task_id: uuid.UUID | None = None

class TaskUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    assignee_id: uuid.UUID | None = None
    priority: TaskPriority | None = None
    due_date: float | None = None
    status: str | None = None
    parent_task_id: uuid.UUID | None = None

class Task(TaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.id", nullable=False)
    parent_task_id: uuid.UUID | None = Field(default=None, foreign_key="task.id")
    project: Project = Relationship(back_populates="tasks")
    subtasks: list["Task"] = Relationship(sa_relationship_kwargs={"remote_side": "Task.id"})
    dependencies: list["TaskDependency"] = Relationship(back_populates="task")
    attachments: list["TaskAttachment"] = Relationship(back_populates="task")
    comments: list["TaskComment"] = Relationship(back_populates="task")

class TaskRead(TaskBase):
    id: uuid.UUID
    project_id: uuid.UUID
    parent_task_id: uuid.UUID | None

# Task Dependency
class TaskDependency(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(foreign_key="task.id")
    depends_on_id: uuid.UUID = Field(foreign_key="task.id")
    task: Task = Relationship(back_populates="dependencies", sa_relationship_kwargs={"foreign_keys": "[TaskDependency.task_id]"})

# Task Attachment
class TaskAttachmentBase(SQLModel):
    file_url: str
    uploaded_by: uuid.UUID = Field(foreign_key="user.id")

class TaskAttachment(TaskAttachmentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(foreign_key="task.id")
    task: Task = Relationship(back_populates="attachments")

# Task Comment
class TaskCommentBase(SQLModel):
    content: str = Field(max_length=2048)
    user_id: uuid.UUID = Field(foreign_key="user.id")

class TaskComment(TaskCommentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(foreign_key="task.id")
    task: Task = Relationship(back_populates="comments")
