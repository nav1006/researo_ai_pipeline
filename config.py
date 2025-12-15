import os
from enum import Enum

class AccessLevel(str, Enum):
    PUBLIC = "public"
    TEACHER_ONLY = "teacher_only"
    SPECIFIC_STUDENTS = "specific_students"
    CLASS_GROUP = "class_group"

class Config:
    SECRET_KEY = "your-super-secret-key-change-in-prod"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    UPLOAD_DIR = "data/uploads"
    CHROMA_DIR = "data/chroma_db"
    OLLAMA_MODEL = "llama3"  # or llama2, mistral, phi
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
