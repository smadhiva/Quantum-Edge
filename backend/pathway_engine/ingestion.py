"""
Pathway Document Ingestion - Live streaming document indexing
Handles PDFs, CSVs, and other financial documents with real-time updates
"""
import pathway as pw
from pathway.stdlib.ml.index import KNNIndex
import os
from typing import Optional
from config import settings

# Try to import embedders with proper fallback
EMBEDDER_AVAILABLE = False
Embedder = None

try:
    from pathway.xpacks.llm import embedders
    
    # Check what embedders are available
    # Common options: OpenAIEmbedder, LiteLLMEmbedder, SentenceTransformerEmbedder
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
    else:
        print(f"⚠️  Available embedders: {[x for x in dir(embedders) if not x.startswith('_')]}")
        EMBEDDER_TYPE = None
except ImportError as e:
    print(f"⚠️  Pathway embedders not available: {e}")
    EMBEDDER_TYPE = None


class DocumentIngestion:
    """
    Live document ingestion using Pathway
    - Monitors folders for new/updated documents
    - Automatically re-indexes on changes
    - Supports PDF, CSV, TXT files
    """
    
    def __init__(self):
        self.docs_path = settings.docs_path
        self.embedder = None
        self.index = None
        self._initialize_embedder()
    
    def _initialize_embedder(self):
        """Initialize embedder for document vectorization"""
        if not EMBEDDER_AVAILABLE:
            print("⚠️  No embedder available - running in text-only mode")
            return
        
        try:
            if EMBEDDER_TYPE == 'LiteLLM' and settings.gemini_api_key:
                # LiteLLM supports multiple providers including Gemini
                self.embedder = Embedder(
                    model="gemini/text-embedding-004",
                    api_key=settings.gemini_api_key
                )
                print("✅ LiteLLM Gemini embedder initialized")
                
            elif EMBEDDER_TYPE == 'OpenAI' and settings.gemini_api_key:
                # Try to use OpenAI-compatible endpoint with Gemini
                self.embedder = Embedder(
                    model="text-embedding-004",
                    api_key=settings.gemini_api_key
                )
                print("✅ OpenAI-compatible embedder initialized")
                
            elif EMBEDDER_TYPE == 'SentenceTransformer':
                # Fallback to local sentence transformer (no API key needed)
                self.embedder = Embedder(
                    model="sentence-transformers/all-MiniLM-L6-v2"
                )
                print("✅ SentenceTransformer embedder initialized (local, no API key needed)")
                
        except Exception as e:
            print(f"⚠️  Failed to initialize embedder: {e}")
            print("   Continuing in text-only mode...")
            self.embedder = None
    
    def create_document_pipeline(self):
        """
        Create Pathway pipeline for document ingestion
        Returns a live-updating document index
        """
        # Ensure directory exists
        os.makedirs(self.docs_path, exist_ok=True)
        
        # Read documents from folder (live monitoring)
        docs = pw.io.fs.read(
            self.docs_path,
            format="binary",
            mode="streaming",
            with_metadata=True
        )
        
        # Parse documents based on file type
        parsed_docs = self._parse_documents(docs)
        
        # Split into chunks
        chunks = self._chunk_documents(parsed_docs)
        
        # Generate embeddings if available
        if self.embedder:
            try:
                embedded_chunks = chunks.select(
                    chunk=pw.this.chunk_text,
                    embedding=self.embedder(pw.this.chunk_text),
                    metadata=pw.this.metadata,
                    source=pw.this.source
                )
                print("✅ Document embeddings enabled")
            except Exception as e:
                print(f"⚠️  Embedding failed: {e}, using text-only mode")
                embedded_chunks = chunks.select(
                    chunk=pw.this.chunk_text,
                    metadata=pw.this.metadata,
                    source=pw.this.source
                )
        else:
            # Without embedder, just return chunks
            embedded_chunks = chunks.select(
                chunk=pw.this.chunk_text,
                metadata=pw.this.metadata,
                source=pw.this.source
            )
        
        return embedded_chunks
    
    def _parse_documents(self, docs):
        """Parse different document types"""
        @pw.udf
        def parse_content(data: bytes, path: str) -> str:
            """Parse document content based on file extension"""
            extension = os.path.splitext(path)[1].lower()
            
            if extension == '.txt':
                return data.decode('utf-8', errors='ignore')
            elif extension == '.csv':
                return data.decode('utf-8', errors='ignore')
            elif extension == '.pdf':
                try:
                    import io
                    from PyPDF2 import PdfReader
                    reader = PdfReader(io.BytesIO(data))
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text
                except Exception as e:
                    return f"Error parsing PDF: {str(e)}"
            elif extension == '.json':
                import json
                try:
                    return json.dumps(json.loads(data.decode('utf-8')), indent=2)
                except:
                    return data.decode('utf-8', errors='ignore')
            else:
                return data.decode('utf-8', errors='ignore')
        
        return docs.select(
            content=parse_content(pw.this.data, pw.this.path),
            metadata=pw.this._metadata,
            source=pw.this.path
        )
    
    def _chunk_documents(self, parsed_docs):
        """Split documents into chunks"""
        @pw.udf
        def split_into_chunks(text: str, max_tokens: int = 500, overlap: int = 50) -> list:
            """Simple chunking by words"""
            words = text.split()
            chunks = []
            
            step = max(1, max_tokens - overlap)
            for i in range(0, len(words), step):
                chunk = ' '.join(words[i:i + max_tokens])
                if chunk.strip():
                    chunks.append(chunk)
            
            return chunks if chunks else [text[:2000]]
        
        chunked = parsed_docs.select(
            chunks=split_into_chunks(pw.this.content),
            metadata=pw.this.metadata,
            source=pw.this.source
        )
        
        flattened = chunked.flatten(pw.this.chunks).select(
            chunk_text=pw.this.chunks,
            metadata=pw.this.metadata,
            source=pw.this.source
        )
        
        return flattened
    
    def create_vector_index(self, embedded_docs):
        """Create KNN index for similarity search"""
        if not self.embedder:
            print("⚠️  No embedder available, cannot create vector index")
            return None
            
        try:
            self.index = KNNIndex(
                embedded_docs.embedding,
                embedded_docs,
                n_dimensions=768,
                n_and=10
            )
            print("✅ Vector index created")
            return self.index
        except Exception as e:
            print(f"⚠️  Failed to create vector index: {e}")
            return None
    
    def query(self, query_text: str, k: int = 5):
        """Query the document index"""
        if not self.embedder or not self.index:
            print("⚠️  Query not available - no embedder or index")
            return []
        
        try:
            query_embedding = self.embedder([query_text])[0]
            results = self.index.query(query_embedding, k=k)
            return results
        except Exception as e:
            print(f"⚠️  Query error: {e}")
            return []


class PortfolioDocumentIngestion(DocumentIngestion):
    """Specialized ingestion for portfolio documents"""
    
    def __init__(self, portfolio_id: str):
        super().__init__()
        self.portfolio_id = portfolio_id
        self.portfolio_docs_path = os.path.join(
            settings.portfolios_path, 
            portfolio_id, 
            "documents"
        )
    
    def create_portfolio_pipeline(self):
        """Create pipeline for portfolio-specific documents"""
        if not os.path.exists(self.portfolio_docs_path):
            os.makedirs(self.portfolio_docs_path, exist_ok=True)
        
        docs = pw.io.fs.read(
            self.portfolio_docs_path,
            format="binary",
            mode="streaming",
            with_metadata=True
        )
        
        parsed_docs = self._parse_documents(docs)
        
        portfolio_docs = parsed_docs.select(
            content=pw.this.content,
            metadata=pw.this.metadata,
            portfolio_id=self.portfolio_id,
            source=pw.this.source
        )
        
        return portfolio_docs


async def start_pathway_pipeline():
    """Start the main Pathway pipeline"""
    print("🚀 Starting Pathway document ingestion pipeline...")
    
    doc_ingestion = DocumentIngestion()
    os.makedirs(settings.docs_path, exist_ok=True)
    
    try:
        embedded_docs = doc_ingestion.create_document_pipeline()
        
        if doc_ingestion.embedder:
            index = doc_ingestion.create_vector_index(embedded_docs)
        
        print("✅ Pipeline created successfully")
        print(f"📁 Monitoring: {settings.docs_path}")
        
        pw.run()
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(start_pathway_pipeline())