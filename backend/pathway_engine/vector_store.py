"""
Pathway Vector Store - Live RAG with streaming updates
"""
import pathway as pw
from pathway.stdlib.ml.index import KNNIndex
from typing import List, Dict, Any, Optional
import os
from config import settings

# Try to import embedders with proper fallback
EMBEDDER_AVAILABLE = False
Embedder = None

try:
    from pathway.xpacks.llm import embedders
    
    if hasattr(embedders, 'LiteLLMEmbedder'):
        Embedder = embedders.LiteLLMEmbedder
        EMBEDDER_TYPE = 'LiteLLM'
        EMBEDDER_AVAILABLE = True
    elif hasattr(embedders, 'OpenAIEmbedder'):
        Embedder = embedders.OpenAIEmbedder
        EMBEDDER_TYPE = 'OpenAI'
        EMBEDDER_AVAILABLE = True
    elif hasattr(embedders, 'SentenceTransformerEmbedder'):
        Embedder = embedders.SentenceTransformerEmbedder
        EMBEDDER_TYPE = 'SentenceTransformer'
        EMBEDDER_AVAILABLE = True
except ImportError:
    EMBEDDER_TYPE = None


class PathwayVectorStore:
    """Live vector store powered by Pathway"""
    
    def __init__(self, embedder=None):
        self.embedder = embedder
        self.index = None
        self.documents = None
        self._initialize()
    
    def _initialize(self):
        """Initialize embedder if not provided"""
        if self.embedder is None and EMBEDDER_AVAILABLE:
            try:
                if EMBEDDER_TYPE == 'SentenceTransformer':
                    self.embedder = Embedder(
                        model="sentence-transformers/all-MiniLM-L6-v2"
                    )
                    print("✅ SentenceTransformer embedder initialized")
                elif EMBEDDER_TYPE == 'LiteLLM' and settings.gemini_api_key:
                    self.embedder = Embedder(
                        model="gemini/text-embedding-004",
                        api_key=settings.gemini_api_key
                    )
                    print("✅ LiteLLM Gemini embedder initialized")
            except Exception as e:
                print(f"⚠️  Failed to initialize embedder: {e}")
    
    def from_folder(self, folder_path: str, file_patterns: List[str] = None):
        """Create vector store from a folder of documents"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
        
        docs = pw.io.fs.read(
            folder_path,
            format="binary",
            mode="streaming",
            with_metadata=True
        )
        
        self.documents = self._process_documents(docs)
        return self
    
    def _process_documents(self, docs):
        """Process and embed documents"""
        
        @pw.udf
        def extract_text(data: bytes, path: str) -> str:
            """Extract text from various file formats"""
            ext = os.path.splitext(path)[1].lower()
            
            try:
                if ext in ['.txt', '.csv']:
                    return data.decode('utf-8', errors='ignore')
                elif ext == '.json':
                    import json
                    content = json.loads(data.decode('utf-8'))
                    return json.dumps(content, indent=2)
                elif ext == '.pdf':
                    import io
                    from PyPDF2 import PdfReader
                    reader = PdfReader(io.BytesIO(data))
                    return "\n".join(page.extract_text() for page in reader.pages)
                else:
                    return data.decode('utf-8', errors='ignore')
            except Exception as e:
                return f"Error: {str(e)}"
        
        @pw.udf
        def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
            """Split text into overlapping chunks"""
            words = text.split()
            chunks = []
            step = max(1, chunk_size - overlap)
            
            for i in range(0, len(words), step):
                chunk = ' '.join(words[i:i + chunk_size])
                if chunk.strip():
                    chunks.append(chunk)
            
            return chunks if chunks else [text[:1000]]
        
        text_docs = docs.select(
            text=extract_text(pw.this.data, pw.this.path),
            path=pw.this.path,
            metadata=pw.this._metadata
        )
        
        chunked_docs = text_docs.select(
            chunks=chunk_text(pw.this.text),
            path=pw.this.path,
            metadata=pw.this.metadata
        ).flatten(pw.this.chunks).select(
            chunk=pw.this.chunks,
            path=pw.this.path,
            metadata=pw.this.metadata
        )
        
        if self.embedder:
            try:
                return chunked_docs.select(
                    chunk=pw.this.chunk,
                    embedding=self.embedder(pw.this.chunk),
                    path=pw.this.path,
                    metadata=pw.this.metadata
                )
            except:
                return chunked_docs
        
        return chunked_docs
    
    async def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform similarity search"""
        if not self.embedder or not self.index:
            return []
        
        try:
            query_embedding = self.embedder([query])[0]
            results = self.index.query(query_embedding, k=k)
            return results
        except Exception as e:
            print(f"⚠️  Search error: {e}")
            return []


class RAGQueryEngine:
    """RAG Query Engine"""
    
    def __init__(self, vector_store: PathwayVectorStore = None, llm=None):
        self.vector_store = vector_store or PathwayVectorStore()
        self.llm = llm
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize Gemini LLM"""
        if self.llm is None and settings.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.gemini_api_key)
                self.llm = genai.GenerativeModel(settings.gemini_model)
                print("✅ Gemini LLM initialized")
            except Exception as e:
                print(f"⚠️  Failed to initialize Gemini LLM: {e}")
    
    async def query(self, question: str, context_limit: int = 5, system_prompt: str = None) -> str:
        """Query with RAG"""
        relevant_docs = await self.vector_store.similarity_search(question, k=context_limit)
        
        if relevant_docs:
            context = "\n\n".join([
                f"Document: {doc.get('path', 'Unknown')}\n{doc.get('chunk', '')}"
                for doc in relevant_docs
            ])
        else:
            context = "No relevant context found."
        
        if system_prompt is None:
            system_prompt = "You are a financial analysis assistant."
        
        full_prompt = f"""{system_prompt}

Context:
{context}

Question: {question}

Answer:"""
        
        if self.llm:
            try:
                response = self.llm.generate_content(full_prompt)
                return response.text
            except Exception as e:
                return f"Error: {e}"
        
        return "LLM not initialized. Configure Gemini API key."
