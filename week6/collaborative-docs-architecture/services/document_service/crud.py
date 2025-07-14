from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from uuid import uuid4
from datetime import datetime
from typing import List, Optional
from .models import Document, DocumentVersion, DocumentPermission, DocumentAnalytics

# Document CRUD
async def create_document(db: AsyncSession, owner_id: str, title: str, content: Optional[str]) -> Document:
    doc = Document(id=str(uuid4()), owner_id=owner_id, title=title, content=content)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    # Create initial version
    version = DocumentVersion(
        id=str(uuid4()),
        document_id=doc.id,
        version_number=1,
        content=content or "",
        diff=None,
        created_at=datetime.utcnow(),
        created_by=owner_id
    )
    db.add(version)
    await db.commit()
    return doc

async def get_document(db: AsyncSession, doc_id: str) -> Optional[Document]:
    stmt = select(Document).where(Document.id == doc_id, Document.is_deleted == False).options(selectinload(Document.versions), selectinload(Document.permissions))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def list_documents(db: AsyncSession, user_id: str, skip: int = 0, limit: int = 10) -> List[Document]:
    stmt = select(Document).where(Document.owner_id == user_id, Document.is_deleted == False).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def update_document(db: AsyncSession, doc: Document, new_title: Optional[str], new_content: Optional[str], user_id: str) -> Document:
    updated = False
    if new_title and new_title != doc.title:
        doc.title = new_title
        updated = True
    if new_content is not None and new_content != doc.content:
        # Diff tracking (simple line diff)
        import difflib
        diff = list(difflib.unified_diff((doc.content or "").splitlines(), (new_content or "").splitlines()))
        version = DocumentVersion(
            id=str(uuid4()),
            document_id=doc.id,
            version_number=len(doc.versions) + 1,
            content=new_content,
            diff=diff,
            created_at=datetime.utcnow(),
            created_by=user_id
        )
        db.add(version)
        doc.content = new_content
        updated = True
    if updated:
        doc.updated_at = datetime.utcnow()
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
    return doc

async def delete_document(db: AsyncSession, doc: Document):
    doc.is_deleted = True
    db.add(doc)
    await db.commit()

# Versioning
async def get_document_versions(db: AsyncSession, doc_id: str) -> List[DocumentVersion]:
    stmt = select(DocumentVersion).where(DocumentVersion.document_id == doc_id).order_by(DocumentVersion.version_number.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

# Permissions
async def add_permission(db: AsyncSession, doc_id: str, user_id: str, permission: str):
    perm = DocumentPermission(id=str(uuid4()), document_id=doc_id, user_id=user_id, permission=permission)
    db.add(perm)
    await db.commit()
    return perm

async def get_permissions(db: AsyncSession, doc_id: str) -> List[DocumentPermission]:
    stmt = select(DocumentPermission).where(DocumentPermission.document_id == doc_id)
    result = await db.execute(stmt)
    return result.scalars().all()

# Analytics
async def log_analytics(db: AsyncSession, doc_id: str, event: str, user_id: Optional[str], details: Optional[dict] = None):
    analytics = DocumentAnalytics(id=str(uuid4()), document_id=doc_id, event=event, user_id=user_id, timestamp=datetime.utcnow(), details=details)
    db.add(analytics)
    await db.commit()
    return analytics

async def get_analytics(db: AsyncSession, doc_id: str) -> List[DocumentAnalytics]:
    stmt = select(DocumentAnalytics).where(DocumentAnalytics.document_id == doc_id)
    result = await db.execute(stmt)
    return result.scalars().all() 