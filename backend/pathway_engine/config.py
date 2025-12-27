"""
Pathway engine configuration
"""
import os
from pathlib import Path

class PathwayConfig:
    """Configuration for Pathway vector indexer"""
    
    # Server settings
    HOST = os.getenv("PATHWAY_HOST", "0.0.0.0")
    PORT = int(os.getenv("PATHWAY_PORT", "8001"))
    
    # Paths
    DOCS_PATH = Path(os.getenv("DOCS_PATH", "./data/documents"))
    VECTOR_DB_PATH = Path(os.getenv("VECTOR_DB_PATH", "./data/vector_db"))
    
    # Embedding settings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # API Keys - FIXED: Added proper fallback values
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDMgAhfKIwe_xEarHd-BnDE13UjF2z0gKI")
    
    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories"""
        cls.DOCS_PATH.mkdir(parents=True, exist_ok=True)
        cls.VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)

config = PathwayConfig()
config.ensure_dirs()

# Debug: Print what keys are loaded (first 10 chars only for security)
if config.OPENAI_API_KEY:
    print(f"🔑 OpenAI API Key loaded: {config.OPENAI_API_KEY[:10]}...")
if config.GEMINI_API_KEY:
    print(f"🔑 Gemini API Key loaded: {config.GEMINI_API_KEY[:10]}...")