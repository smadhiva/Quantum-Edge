"""
Simple vector store without Pathway dependency
Uses sentence-transformers for embeddings
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer


class SimpleVectorStore:
    """
    Simple in-memory vector store
    """
    
    def __init__(self, docs_path: str = "./data/documents"):
        self.docs_path = Path(docs_path)
        self.docs_path.mkdir(parents=True, exist_ok=True)
        
        # Use free embedding model
        print("📚 Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.documents = []
        self.embeddings = []
        
        self._load_documents()
    
    def _load_documents(self):
        """Load and embed all documents"""
        print(f"📖 Loading documents from {self.docs_path}")
        
        for file_path in self.docs_path.glob("**/*"):
            if file_path.is_file() and file_path.suffix in ['.txt', '.md']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Chunk large documents
                    chunks = self._chunk_text(content)
                    
                    for i, chunk in enumerate(chunks):
                        embedding = self.model.encode(chunk)
                        
                        self.documents.append({
                            'id': f"{file_path.stem}_{i}",
                            'source': str(file_path),
                            'content': chunk,
                            'metadata': {
                                'filename': file_path.name,
                                'chunk': i
                            }
                        })
                        self.embeddings.append(embedding)
                
                except Exception as e:
                    print(f"⚠️  Error loading {file_path}: {e}")
        
        print(f"✅ Loaded {len(self.documents)} document chunks")
    
    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks if chunks else [text]
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        """
        if not self.documents:
            return []
        
        # Embed query
        query_embedding = self.model.encode(query)
        
        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )
            similarities.append((i, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k results
        results = []
        for idx, score in similarities[:top_k]:
            doc = self.documents[idx].copy()
            doc['score'] = float(score)
            results.append(doc)
        
        return results
    
    def add_document(self, content: str, metadata: Dict = None):
        """Add a new document"""
        embedding = self.model.encode(content)
        
        doc_id = f"doc_{len(self.documents)}"
        self.documents.append({
            'id': doc_id,
            'content': content,
            'metadata': metadata or {}
        })
        self.embeddings.append(embedding)
        
        return doc_id


# Global instance
_vector_store = None

def get_vector_store() -> SimpleVectorStore:
    """Get or create vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = SimpleVectorStore()
    return _vector_store