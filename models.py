from pydantic import BaseModel, EmailStr
from typing import List, Optional
from config import AccessLevel
from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: UserRole

class User(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole

class DocumentCreate(BaseModel):
    filename: str
    access_level: AccessLevel
    allowed_student_ids: Optional[List[str]] = []
    class_group: Optional[str] = None

class QueryRequest(BaseModel):
    query: str
    user_token: str  # JWT token
