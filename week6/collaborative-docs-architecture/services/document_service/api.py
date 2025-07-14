from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .core import get_current_user
from .crud import (
    create_document, get_document, list_documents, update_document, delete_document,
    get_document_versions, add_permission, get_permissions, log_analytics, get_analytics
)
from .schemas import (
    DocumentCreate, DocumentUpdate, DocumentOut, DocumentVersionOut, ShareRequest, Collaborator, SearchRequest, SearchResult, ErrorResponse, AnalyticsEvent
)
from .utils import cache_document, get_cached_document, cache_search_results, get_cached_search_results
import os
from fastapi.responses import FileResponse, StreamingResponse
import shutil

router = APIRouter(prefix="/documents", tags=["Documents"])

# Dependency placeholder for DB session
async def get_db():
    # Should be replaced with actual session logic
    raise NotImplementedError

FILES_DIR = os.path.join(os.path.dirname(__file__), 'files')
os.makedirs(FILES_DIR, exist_ok=True)

@router.post("/", response_model=DocumentOut, responses={401: {"model": ErrorResponse}})
async def create_doc(doc_in: DocumentCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    doc = await create_document(db, owner_id=user["user_id"], title=doc_in.title, content=doc_in.content)
    return doc

@router.get("/", response_model=List[DocumentOut], responses={401: {"model": ErrorResponse}})
async def list_docs(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    docs = await list_documents(db, user_id=user["user_id"], skip=skip, limit=limit)
    return docs

@router.get("/{doc_id}", response_model=DocumentOut, responses={404: {"model": ErrorResponse}})
async def get_doc(doc_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    cached = await get_cached_document(doc_id)
    if cached:
        return cached
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    # Optionally: convert ORM to Pydantic
    doc_out = DocumentOut.from_orm(doc)
    await cache_document(doc_id, doc_out.dict())
    return doc_out

@router.put("/{doc_id}", response_model=DocumentOut, responses={404: {"model": ErrorResponse}})
async def update_doc(doc_id: str, doc_in: DocumentUpdate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = await update_document(db, doc, doc_in.title, doc_in.content, user["user_id"])
    return doc

@router.delete("/{doc_id}", status_code=204, responses={404: {"model": ErrorResponse}})
async def delete_doc(doc_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await delete_document(db, doc)
    return

@router.get("/{doc_id}/versions", response_model=List[DocumentVersionOut], responses={404: {"model": ErrorResponse}})
async def get_versions(doc_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    versions = await get_document_versions(db, doc_id)
    return versions

@router.post("/{doc_id}/share", status_code=204, responses={404: {"model": ErrorResponse}})
async def share_doc(doc_id: str, req: ShareRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    for uid in req.user_ids:
        await add_permission(db, doc_id, uid, req.permission)
    return

@router.get("/{doc_id}/collaborators", response_model=List[Collaborator], responses={404: {"model": ErrorResponse}})
async def get_collaborators(doc_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    perms = await get_permissions(db, doc_id)
    return [Collaborator(user_id=p.user_id, role=p.permission, added_at=None) for p in perms]

@router.get("/search", response_model=List[SearchResult], responses={401: {"model": ErrorResponse}})
async def search_docs(q: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    cached = await get_cached_search_results(user["user_id"], q)
    if cached:
        return cached
    # Placeholder for search logic
    results = []
    await cache_search_results(user["user_id"], q, results)
    return results

@router.post("/{doc_id}/upload", status_code=204, responses={404: {"model": ErrorResponse}})
async def upload_file(doc_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    file_path = os.path.join(FILES_DIR, f"{doc_id}")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return

@router.get("/{doc_id}/download", response_class=FileResponse, responses={404: {"model": ErrorResponse}})
async def download_file(doc_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    file_path = os.path.join(FILES_DIR, f"{doc_id}")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=f"document_{doc_id}")

@router.post("/{doc_id}/analytics", status_code=204, responses={404: {"model": ErrorResponse}})
async def log_doc_analytics(doc_id: str, event: AnalyticsEvent, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await log_analytics(db, doc_id, event.event, user["user_id"], event.details)
    return

@router.get("/{doc_id}/analytics", response_model=List[AnalyticsEvent], responses={404: {"model": ErrorResponse}})
async def get_doc_analytics(doc_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    analytics = await get_analytics(db, doc_id)
    return [AnalyticsEvent(event=a.event, user_id=a.user_id, timestamp=a.timestamp, details=a.details) for a in analytics]

@router.post("/{doc_id}/backup", status_code=200, responses={404: {"model": ErrorResponse}})
async def backup_document(doc_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    backup_path = os.path.join(FILES_DIR, f"{doc_id}.bak")
    # Backup DB content
    with open(backup_path, "w") as f:
        import json
        f.write(json.dumps({"id": doc.id, "title": doc.title, "content": doc.content}))
    # Backup file if exists
    file_path = os.path.join(FILES_DIR, f"{doc_id}")
    if os.path.exists(file_path):
        shutil.copy(file_path, backup_path + ".file")
    return {"success": True, "backup": backup_path}

@router.post("/{doc_id}/restore", status_code=200, responses={404: {"model": ErrorResponse}})
async def restore_document(doc_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    backup_path = os.path.join(FILES_DIR, f"{doc_id}.bak")
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")
    with open(backup_path, "r") as f:
        import json
        data = json.load(f)
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.title = data["title"]
    doc.content = data["content"]
    db.add(doc)
    await db.commit()
    # Restore file if exists
    file_backup = backup_path + ".file"
    file_path = os.path.join(FILES_DIR, f"{doc_id}")
    if os.path.exists(file_backup):
        shutil.copy(file_backup, file_path)
    return {"success": True}

@router.post("/{doc_id}/clone", response_model=DocumentOut, responses={404: {"model": ErrorResponse}})
async def clone_document(doc_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    from uuid import uuid4
    new_id = str(uuid4())
    new_doc = await create_document(db, owner_id=user["user_id"], title=doc.title + " (Clone)", content=doc.content)
    # Clone file if exists
    file_path = os.path.join(FILES_DIR, f"{doc_id}")
    new_file_path = os.path.join(FILES_DIR, f"{new_id}")
    if os.path.exists(file_path):
        shutil.copy(file_path, new_file_path)
    return new_doc

@router.get("/{doc_id}/export", responses={404: {"model": ErrorResponse}})
async def export_document(doc_id: str, format: str = "pdf", db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    # Placeholder: just return content as a file in requested format
    from io import BytesIO
    content = doc.content or ""
    if format == "pdf":
        # Use a real PDF library in production
        data = content.encode()
        filename = f"{doc_id}.pdf"
    elif format == "docx":
        data = content.encode()
        filename = f"{doc_id}.docx"
    else:
        data = content.encode()
        filename = f"{doc_id}.html"
    return StreamingResponse(BytesIO(data), media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={filename}"}) 