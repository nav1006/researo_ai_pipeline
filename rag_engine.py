# rag_engine.py
import os
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_community.vectorstores import Chroma
from config import config


class RAGEngine:
    def __init__(self):
        """Initialize RAG engine with Ollama"""
        print("Initializing RAG Engine...")
        print("Loading embedding model (first run may take a minute)...")

        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        print(f"Connecting to Ollama ({config.LLM_MODEL})...")
        self.llm = OllamaLLM(
            base_url=config.OLLAMA_BASE_URL,
            model=config.LLM_MODEL,
            temperature=0.7
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )

        self.teacher_vectorstore = None
        self.student_vectorstore = None

    def load_documents_from_folder(self, folder_path: str) -> List:
        """Load documents from folder"""
        documents = []

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            return documents

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            if not os.path.isfile(file_path):
                continue

            try:
                if filename.endswith('.pdf'):
                    loader = PyPDFLoader(file_path)
                elif filename.endswith('.txt') or filename.endswith('.md'):
                    loader = TextLoader(file_path)
                elif filename.endswith('.docx'):
                    loader = Docx2txtLoader(file_path)
                else:
                    continue

                docs = loader.load()
                for doc in docs:
                    doc.metadata['source_file'] = filename
                documents.extend(docs)
                print(f"  ✓ {filename}")

            except Exception as e:
                print(f"  ✗ Error loading {filename}: {e}")

        return documents

    def index_documents(self):
        """Index documents from folders"""
        print("\nLoading teacher documents...")
        teacher_docs = self.load_documents_from_folder(config.TEACHER_FOLDER)

        print("\nLoading student documents...")
        student_docs = self.load_documents_from_folder(config.STUDENT_FOLDER)

        if teacher_docs:
            teacher_chunks = self.text_splitter.split_documents(teacher_docs)
            print(f"\nCreating embeddings for {len(teacher_chunks)} teacher chunks...")

            self.teacher_vectorstore = Chroma.from_documents(
                documents=teacher_chunks,
                embedding=self.embeddings,
                collection_name="teacher_docs",
                persist_directory=f"{config.CHROMA_PERSIST_DIR}/teacher"
            )

        if student_docs:
            student_chunks = self.text_splitter.split_documents(student_docs)
            print(f"Creating embeddings for {len(student_chunks)} student chunks...")

            self.student_vectorstore = Chroma.from_documents(
                documents=student_chunks,
                embedding=self.embeddings,
                collection_name="student_docs",
                persist_directory=f"{config.CHROMA_PERSIST_DIR}/student"
            )

    def load_existing_index(self):
        """Load existing indices"""
        try:
            teacher_path = f"{config.CHROMA_PERSIST_DIR}/teacher"
            if os.path.exists(teacher_path):
                self.teacher_vectorstore = Chroma(
                    collection_name="teacher_docs",
                    embedding_function=self.embeddings,
                    persist_directory=teacher_path
                )
        except:
            pass

        try:
            student_path = f"{config.CHROMA_PERSIST_DIR}/student"
            if os.path.exists(student_path):
                self.student_vectorstore = Chroma(
                    collection_name="student_docs",
                    embedding_function=self.embeddings,
                    persist_directory=student_path
                )
        except:
            pass

    def query(self, query: str, user_role: str) -> Dict:
        """Query with role-based access control"""
        vectorstores = []

        if user_role == "teacher":
            if self.teacher_vectorstore:
                vectorstores.append(("teacher", self.teacher_vectorstore))
            if self.student_vectorstore:
                vectorstores.append(("student", self.student_vectorstore))
        else:
            if self.student_vectorstore:
                vectorstores.append(("student", self.student_vectorstore))

        if not vectorstores:
            return {
                "answer": "No documents available. Please index documents first.",
                "sources": []
            }

        all_docs = []
        for source_type, vectorstore in vectorstores:
            docs = vectorstore.similarity_search(query, k=config.TOP_K_RESULTS)
            for doc in docs:
                doc.metadata['access_level'] = source_type
            all_docs.extend(docs)

        if not all_docs:
            return {
                "answer": "I couldn't find relevant information to answer your question.",
                "sources": []
            }

        all_docs = all_docs[:config.TOP_K_RESULTS]

        context = "\n\n".join([
            f"[Document: {doc.metadata.get('source_file', 'Unknown')}]\n{doc.page_content}"
            for doc in all_docs
        ])

        prompt = f"""You are a helpful AI assistant that answers questions based on provided context.

INSTRUCTIONS:
1. Read the context carefully
2. Answer based ONLY on the context
3. DO NOT quote directly - synthesize the information
4. Use clear, professional language
5. Format with paragraphs and bullet points
6. If context is insufficient, say so

CONTEXT:
{context}

QUESTION: {query}

ANSWER:"""

        response = self.llm.invoke(prompt)

        sources = [
            {
                "file": doc.metadata.get('source_file', 'Unknown'),
                "access_level": doc.metadata.get('access_level', 'unknown')
            }
            for doc in all_docs
        ]

        return {
            "answer": response,
            "sources": sources
        }


# Global instance
rag_engine = RAGEngine()
