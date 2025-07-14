from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text, JSON, func
from uuid import uuid4
from datetime import datetime

Base = declarative_base(cls=AsyncAttrs)

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    owner_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    versions = relationship("DocumentVersion", back_populates="document")
    permissions = relationship("DocumentPermission", back_populates="document")
    analytics = relationship("DocumentAnalytics", back_populates="document")

class DocumentVersion(Base):
    __tablename__ = "document_versions"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    diff = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String, nullable=False)
    document = relationship("Document", back_populates="versions")

class DocumentPermission(Base):
    __tablename__ = "document_permissions"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    user_id = Column(String, nullable=False)
    permission = Column(String, nullable=False)  # read, write, admin
    document = relationship("Document", back_populates="permissions")

class DocumentCollaborator(Base):
    __tablename__ = "document_collaborators"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    user_id = Column(String, nullable=False)
    role = Column(String, nullable=False)  # e.g., editor, viewer
    added_at = Column(DateTime, default=func.now())

class DocumentAnalytics(Base):
    __tablename__ = "document_analytics"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    event = Column(String, nullable=False)  # view, edit, share, etc.
    user_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=func.now())
    details = Column(JSON, nullable=True)
    document = relationship("Document", back_populates="analytics") 