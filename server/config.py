import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Llama API
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
LLAMA_API_URL = os.getenv("LLAMA_API_URL", "https://api.llama.com/v1/chat/completions")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "Llama-4-Maverick-17B-128E-Instruct-FP8")

# ChromaDB / RAG
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_DIR = str(BASE_DIR / "chroma_db")
COLLECTION_NAME = "ai_detection_knowledge"
DEFAULT_CSV = BASE_DIR / "AI_Human.csv"
RAG_TOP_K = 3

# CORS
CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

# Humanization
HUMANIZE_MAX_ATTEMPTS = 3
