import os
import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import ollama

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader

from config import Config
from auth import decode_token

config = Config()

client = chromadb.PersistentClient(
    path=config.CHROMA_DIR,
    settings=Settings(anonymized_telemetry=False),
)

embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)

teacher_collection = client.get_or_create_collection(
    name="teacher_docs",
    metadata={"hnsw:space": "cosine"},
)

student_collection = client.get_or_create_collection(
    name="student_docs",
    metadata={"hnsw:space": "cosine"},
)


async def store_document(file_path: str, doc_id: str, access_level: str,
                         allowed_student_ids: list, class_group: str | None = None):
    if file_path.lower().endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path)

    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    texts = [c.page_content for c in chunks]
    embeddings = embedding_model.encode(texts).tolist()

    json_allowed_ids = json.dumps(allowed_student_ids or [])

    metadatas = []
    for _ in chunks:
        metadatas.append(
            {
                "document_id": doc_id,
                "access_level": access_level,
                "allowed_student_ids": json_allowed_ids,
                "class_group": class_group or "",
                "filename": os.path.basename(file_path),
            }
        )

    ids_teacher = [f"{doc_id}_t_{i}" for i in range(len(chunks))]
    teacher_collection.add(
        ids=ids_teacher,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    if access_level == "public":
        ids_student = [f"{doc_id}_s_{i}" for i in range(len(chunks))]
        student_collection.add(
            ids=ids_student,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )


def build_rag_filter(user_token: str, user_id: str, user_classes: list) -> dict:
    payload = decode_token(user_token)
    if not payload:
        return {}

    user_role = payload.get("role")
    if user_role in ["teacher", "admin"]:
        return {}

    return {
        "or": [
            {"key": "access_level", "match": {"value": "public"}},
            # NOTE: Filtering on allowed_student_ids list is limited by Chroma capabilities
            {
                "and": [
                    {"key": "access_level", "match": {"value": "specific_students"}},
                ]
            },
            {
                "and": [
                    {"key": "access_level", "match": {"value": "class_group"}},
                    {"key": "class_group", "in": user_classes}
                ]
            }
        ]
    }


async def query_rag(query: str, user_token: str, user_id: str, user_classes: list = [], k: int = 5):
    filter = build_rag_filter(user_token, user_id, user_classes)

    query_embedding = embedding_model.encode([query]).tolist()

    teacher_kwargs = {
        "query_embeddings": query_embedding,
        "n_results": k,
    }
    if filter:
        teacher_kwargs["where"] = filter

    teacher_results = teacher_collection.query(**teacher_kwargs)

    payload = decode_token(user_token)
    user_role = payload.get("role") if payload else "student"
    if user_role == "student":
        student_results = student_collection.query(
            query_embeddings=query_embedding,
            n_results=k,
            where={"access_level": "public"},
        )
        if teacher_results["documents"] and teacher_results["documents"][0]:
            teacher_results["documents"][0].extend(student_results["documents"][0])
            teacher_results["metadatas"][0].extend(student_results["metadatas"][0])
            teacher_results["distances"][0].extend(student_results["distances"][0])
        else:
            teacher_results = student_results

    if (
        not teacher_results
        or not teacher_results["documents"]
        or not teacher_results["documents"][0]
    ):
        return "Insufficient information provided.", []

    chunks = teacher_results["documents"][0][:5]
    context = "\n\n".join([f"Source {i}:\n{c}" for i, c in enumerate(chunks)])

    system_prompt = """
You are an expert educational assistant.

Answer ONLY based on the following context extracted from documents.
Do NOT quote verbatim, but synthesize information naturally into well-structured, clear, and concise paragraphs or bullet points.

If the context is insufficient to answer, say 'Insufficient information provided.'
"""

    response = ollama.chat(
        model=config.OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
    )

    metadatas = teacher_results["metadatas"][0]
    distances = teacher_results["distances"][0]

    sources = []
    for i, meta in enumerate(metadatas[:5]):
        sources.append(
            {
                "document_id": meta.get("document_id"),
                "filename": meta.get("filename"),
                "access_level": meta.get("access_level"),
                "score": 1 - distances[i],
            }
        )

    return response["message"]["content"], sources
