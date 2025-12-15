import os
import uuid
import json

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles

from models import UserCreate, QueryRequest, UserRole
from auth import hash_password, verify_password, create_access_token, decode_token
from rag_engine import store_document, query_rag
from config import Config

config = Config()
app = FastAPI(title="RAG RBAC Production - PyCharm")

# In-memory stores for PoC
users: dict[str, dict] = {}
docs: dict[str, dict] = {}

os.makedirs(config.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")


@app.on_event("startup")
async def startup():
    # Create test users on startup to enable immediate logins
    print("🚀 Starting RAG RBAC app...")

    teacher_id = str(uuid.uuid4())
    users[teacher_id] = {
        "id": teacher_id,
        "email": "teacher@test.com",
        "password_hash": hash_password("pass123"),
        "name": "Mr. Smith",
        "role": UserRole.TEACHER.value,
    }

    student_id = str(uuid.uuid4())
    users[student_id] = {
        "id": student_id,
        "email": "student@test.com",
        "password_hash": hash_password("pass123"),
        "name": "John Doe",
        "role": UserRole.STUDENT.value,
    }

    print("\n🎯 TEST USERS READY:")
    print("  Teacher: teacher@test.com / pass123")
    print("  Student: student@test.com / pass123")
    print("\nOpen Swagger UI at: http://127.0.0.1:8000/docs")


@app.post("/auth/register")
async def register(user_data: UserCreate):
    if any(u["email"] == user_data.email for u in users.values()):
        raise HTTPException(400, "User already exists")

    user_id = str(uuid.uuid4())
    users[user_id] = {
        "id": user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "role": user_data.role.value,
    }

    token = create_access_token(user_id, user_data.role.value)
    return {"access_token": token, "role": user_data.role}


@app.post("/auth/login")
async def login(email: str = Form(...), password: str = Form(...)):
    for user_id, user in users.items():
        if user["email"] == email:
            if not verify_password(password, user["password_hash"]):
                break
            token = create_access_token(user_id, user["role"])
            return {"access_token": token, "role": user["role"]}
    raise HTTPException(401, "Invalid credentials")


@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    access_level: str = Form("public"),
    allowed_student_ids: str = Form("[]"),
    class_group: str = Form(""),
    token: str = Form(...),
):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")

    role = payload.get("role")
    uploader_id = payload.get("sub")

    if role not in [UserRole.TEACHER.value, UserRole.ADMIN.value]:
        raise HTTPException(403, "Only teachers/admins can upload")

    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    saved_path = os.path.join(config.UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(saved_path, "wb") as f:
        f.write(await file.read())

    try:
        allowed_ids = json.loads(allowed_student_ids) if allowed_student_ids else []
    except json.JSONDecodeError:
        raise HTTPException(400, "allowed_student_ids must be a JSON list")

    doc_id = str(uuid.uuid4())
    docs[doc_id] = {
        "id": doc_id,
        "filename": file.filename,
        "file_path": saved_path,
        "uploader_id": uploader_id,
        "access_level": access_level,
        "allowed_student_ids": allowed_ids,
        "class_group": class_group,
    }

    await store_document(saved_path, doc_id, access_level, allowed_ids, class_group)

    return {"document_id": doc_id, "message": f"Document uploaded with {access_level} access"}


@app.post("/query")
async def query(request: QueryRequest):
    token_payload = decode_token(request.user_token)
    if not token_payload:
        raise HTTPException(401, "Invalid or expired token")

    user_id = token_payload.get("sub")
    # In real system, get actual user classes from DB; here use empty list for demo
    user_classes = []

    answer, sources = await query_rag(request.query, request.user_token, user_id, user_classes)
    return {"answer": answer, "sources": sources}


@app.get("/")
async def root():
    return {"message": "RAG RBAC app is running. Visit /docs to interact."}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
