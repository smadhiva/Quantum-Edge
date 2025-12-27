"""
Pathway Document Ingestion - Live streaming document indexing
Handles PDFs, CSVs, and other financial documents with real-time updates
"""
import pathway as pw
from pathway.stdlib.ml.index import KNNIndex
from pathway.xpacks.llm.embedders import GeminiEmbedder
from pathway.xpacks.llm.splitters import TokenCountSplitter
import os
from typing import Optional
from config import settings


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
        """Initialize Gemini embedder for document vectorization"""
        if settings.gemini_api_key:
            self.embedder = GeminiEmbedder(
                api_key=settings.gemini_api_key,
                model="models/embedding-001"
            )
    
    def create_document_pipeline(self):
        """
        Create Pathway pipeline for document ingestion
        Returns a live-updating document index
        """
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
        splitter = TokenCountSplitter(
            min_tokens=100,
            max_tokens=500
        )
        chunks = parsed_docs.select(
            chunks=splitter(pw.this.content)
        ).flatten(pw.this.chunks)
        
        # Generate embeddings
        if self.embedder:
            embedded_chunks = chunks.select(
                chunk=pw.this.chunks,
                embedding=self.embedder(pw.this.chunks),
                metadata=pw.this.metadata
            )
        else:
            embedded_chunks = chunks
        
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
                # PDF parsing requires pypdf2
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
                return json.dumps(json.loads(data.decode('utf-8')), indent=2)
            else:
                return data.decode('utf-8', errors='ignore')
        
        return docs.select(
            content=parse_content(pw.this.data, pw.this.path),
            metadata=pw.this._metadata
        )
    
    def create_vector_index(self, embedded_docs):
        """Create KNN index for similarity search"""
        self.index = KNNIndex(
            embedded_docs.embedding,
            embedded_docs,
            n_dimensions=768,  # Gemini embedding dimension
            n_and_m_neighbors=(10, 20)
        )
        return self.index
    
    def query(self, query_text: str, k: int = 5):
        """Query the document index"""
        if not self.embedder or not self.index:
            return []
        
        query_embedding = self.embedder([query_text])[0]
        results = self.index.query(query_embedding, k=k)
        return results


class PortfolioDocumentIngestion(DocumentIngestion):
    """
    Specialized ingestion for portfolio documents
    - Annual reports
    - Earnings transcripts
    - Analyst reports
    """
    
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
        
        # Add portfolio context
        portfolio_docs = parsed_docs.select(
            content=pw.this.content,
            metadata=pw.this.metadata,
            portfolio_id=self.portfolio_id
        )
        
        return portfolio_docs


async def start_pathway_pipeline():
    """
    Start the main Pathway pipeline
    This runs continuously and handles all document updates
    """
    print("🚀 Starting Pathway document ingestion pipeline...")
    
    # Create document ingestion
    doc_ingestion = DocumentIngestion()
    
    # Ensure docs directory exists
    os.makedirs(settings.docs_path, exist_ok=True)
    
    # Create pipeline
    embedded_docs = doc_ingestion.create_document_pipeline()
    
    # Create index
    index = doc_ingestion.create_vector_index(embedded_docs)
    
    # Run pipeline (this blocks)
    pw.run()


# For direct execution
if __name__ == "__main__":
    import asyncio
    asyncio.run(start_pathway_pipeline())
