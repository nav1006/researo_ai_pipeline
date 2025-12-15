import aiosqlite
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

DB_PATH = "data/users.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                password_hash TEXT,
                name TEXT,
                role TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT,
                file_path TEXT,
                uploader_id TEXT,
                access_level TEXT,
                allowed_student_ids TEXT,
                class_group TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

user_db: Dict[str, Dict] = {}
doc_db: Dict[str, Dict] = {}

async def get_user_db():
    return user_db

async def get_doc_db():
    return doc_db
