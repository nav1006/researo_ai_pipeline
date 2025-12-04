# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Ollama settings
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3")

    # Embedding model (local)
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # Document folders
    TEACHER_FOLDER = "./documents/teacher"
    STUDENT_FOLDER = "./documents/student"

    # ChromaDB settings
    CHROMA_PERSIST_DIR = "./chroma_db"

    # RAG settings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    TOP_K_RESULTS = 5


config = Config()
