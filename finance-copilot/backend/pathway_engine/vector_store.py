"""
Pathway Vector Store - Live RAG with streaming updates
"""
import pathway as pw
from pathway.stdlib.ml.index import KNNIndex
from typing import List, Dict, Any, Optional
import os
from config import settings


class PathwayVectorStore:
    """
    Live vector store powered by Pathway
    - Real-time document indexing
    - Automatic updates on file changes
    - Efficient similarity search
    """
    
    def __init__(self, embedder=None):
        self.embedder = embedder
        self.index = None
        self.documents = None
        self._initialize()
    
    def _initialize(self):
        """Initialize embedder if not provided"""
        if self.embedder is None and settings.gemini_api_key:
            try:
                from pathway.xpacks.llm.embedders import GeminiEmbedder
                self.embedder = GeminiEmbedder(
                    api_key=settings.gemini_api_key,
                    model="models/embedding-001"
                )
            except Exception as e:
                print(f"Failed to initialize Gemini embedder: {e}")
    
    def from_folder(self, folder_path: str, file_patterns: List[str] = None):
        """
        Create vector store from a folder of documents
        Monitors folder for live updates
        """
        if file_patterns is None:
            file_patterns = ["*.pdf", "*.txt", "*.csv", "*.json"]
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
        
        # Read documents with streaming mode
        docs = pw.io.fs.read(
            folder_path,
            format="binary",
            mode="streaming",
            with_metadata=True
        )
        
        # Process and embed documents
        self.documents = self._process_documents(docs)
        
        return self
    
    def _process_documents(self, docs):
        """Process and embed documents"""
        
        @pw.udf
        def extract_text(data: bytes, path: str) -> str:
            """Extract text from various file formats"""
            ext = os.path.splitext(path)[1].lower()
            
            try:
                if ext == '.txt':
                    return data.decode('utf-8', errors='ignore')
                elif ext == '.csv':
                    return data.decode('utf-8', errors='ignore')
                elif ext == '.json':
                    import json
                    content = json.loads(data.decode('utf-8'))
                    return json.dumps(content, indent=2)
                elif ext == '.pdf':
                    import io
                    from PyPDF2 import PdfReader
                    reader = PdfReader(io.BytesIO(data))
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text
                else:
                    return data.decode('utf-8', errors='ignore')
            except Exception as e:
                return f"Error: {str(e)}"
        
        @pw.udf
        def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
            """Split text into overlapping chunks"""
            words = text.split()
            chunks = []
            
            for i in range(0, len(words), chunk_size - overlap):
                chunk = ' '.join(words[i:i + chunk_size])
                if chunk:
                    chunks.append(chunk)
            
            return chunks if chunks else [text[:1000]]  # Fallback
        
        # Extract text
        text_docs = docs.select(
            text=extract_text(pw.this.data, pw.this.path),
            path=pw.this.path,
            metadata=pw.this._metadata
        )
        
        # Chunk documents
        chunked_docs = text_docs.select(
            chunks=chunk_text(pw.this.text),
            path=pw.this.path,
            metadata=pw.this.metadata
        ).flatten(pw.this.chunks)
        
        # Embed chunks if embedder available
        if self.embedder:
            embedded_docs = chunked_docs.select(
                chunk=pw.this.chunks,
                embedding=self.embedder(pw.this.chunks),
                path=pw.this.path,
                metadata=pw.this.metadata
            )
            return embedded_docs
        
        return chunked_docs
    
    def create_index(self, n_dimensions: int = 768):
        """Create KNN index for similarity search"""
        if self.documents is None:
            raise ValueError("No documents loaded. Call from_folder first.")
        
        self.index = KNNIndex(
            self.documents.embedding,
            self.documents,
            n_dimensions=n_dimensions,
            n_and_m_neighbors=(10, 20)
        )
        
        return self.index
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search on the vector store
        """
        if not self.embedder:
            return []
        
        # Get query embedding
        query_embedding = self.embedder([query])[0]
        
        # Search index
        if self.index:
            results = self.index.query(query_embedding, k=k)
            return results
        
        return []
    
    def add_documents(self, documents: List[Dict[str, str]]):
        """
        Add documents to the vector store
        Note: In Pathway, this is typically done by adding files to the monitored folder
        """
        for doc in documents:
            if 'content' in doc and 'filename' in doc:
                filepath = os.path.join(settings.docs_path, doc['filename'])
                with open(filepath, 'w') as f:
                    f.write(doc['content'])
    
    def delete_document(self, filename: str):
        """
        Delete a document from the vector store
        """
        filepath = os.path.join(settings.docs_path, filename)
        if os.path.exists(filepath):
            os.remove(filepath)


class RAGQueryEngine:
    """
    RAG Query Engine using Pathway Vector Store + Gemini LLM
    """
    
    def __init__(self, vector_store: PathwayVectorStore, llm=None):
        self.vector_store = vector_store
        self.llm = llm
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize Gemini LLM"""
        if self.llm is None and settings.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.gemini_api_key)
                self.llm = genai.GenerativeModel(settings.gemini_model)
            except Exception as e:
                print(f"Failed to initialize Gemini LLM: {e}")
    
    async def query(
        self, 
        question: str, 
        context_limit: int = 5,
        system_prompt: str = None
    ) -> str:
        """
        Query with RAG - retrieves relevant context and generates answer
        """
        # Retrieve relevant documents
        relevant_docs = await self.vector_store.similarity_search(question, k=context_limit)
        
        # Build context
        context = "\n\n".join([
            f"Document: {doc.get('path', 'Unknown')}\n{doc.get('chunk', '')}"
            for doc in relevant_docs
        ])
        
        # Create prompt
        if system_prompt is None:
            system_prompt = """You are a financial analysis assistant. 
            Use the provided context to answer questions accurately.
            If the context doesn't contain relevant information, say so."""
        
        full_prompt = f"""{system_prompt}

Context:
{context}

Question: {question}

Answer:"""
        
        # Generate response
        if self.llm:
            response = self.llm.generate_content(full_prompt)
            return response.text
        
        return "LLM not initialized. Please configure Gemini API key."
    
    async def query_with_sources(
        self, 
        question: str, 
        context_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Query with RAG and return sources
        """
        relevant_docs = await self.vector_store.similarity_search(question, k=context_limit)
        
        answer = await self.query(question, context_limit)
        
        sources = [
            {"path": doc.get('path', 'Unknown'), "relevance": doc.get('score', 0)}
            for doc in relevant_docs
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "context_used": len(relevant_docs)
        }
