"""
Pathway Vector Indexer Server
Based on: https://github.com/pathwaycom/llm-app
"""
import pathway as pw
from pathway.xpacks.llm import embedders, vector_store
import os
import sys

from .config import config


class SimpleVectorIndexer:
    """
    Simple vector indexer using Pathway
    """
    
    def __init__(self):
        self.embedder = None
        self.vector_server = None
        self._setup_embedder()
    
    def _setup_embedder(self):
        """Setup embedding model with smart fallback"""
        
        # Try OpenAI first if API key is available
        if config.OPENAI_API_KEY:
            try:
                print("🔄 Attempting to use OpenAI embeddings...")
                self.embedder = embedders.OpenAIEmbedder(
                    api_key=config.OPENAI_API_KEY,
                    model=config.EMBEDDING_MODEL
                )
                # Test if it works by creating a test embedding
                print("✅ OpenAI embeddings initialized successfully")
                return
            except Exception as e:
                print(f"⚠️  OpenAI embeddings failed: {str(e)[:100]}")
                print("🔄 Falling back to local SentenceTransformer...")
        
        # Fallback to SentenceTransformer (free, local)
        try:
            print("📦 Using local SentenceTransformer embeddings (free, no API costs)")
            self.embedder = embedders.SentenceTransformerEmbedder(
                model="sentence-transformers/all-MiniLM-L6-v2"
            )
            print("✅ SentenceTransformer embeddings initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize any embedder: {e}")
            raise
    
    def setup_vector_store(self, docs_path: str = None):
        """
        Setup vector store from documents directory
        """
        docs_path = docs_path or str(config.DOCS_PATH)
        
        print(f"📚 Indexing documents from: {docs_path}")
        
        # Ensure directory exists
        os.makedirs(docs_path, exist_ok=True)
        
        # Create document stream from files
        documents = pw.io.fs.read(
            path=docs_path,
            format="binary",
            mode="streaming",
            with_metadata=True
        )
        
        try:
            # Create vector store server
            self.vector_server = vector_store.VectorStoreServer(
                documents,
                embedder=self.embedder,
            )
            print("✅ Vector store initialized")
            return self.vector_server
            
        except Exception as e:
            # If OpenAI quota exceeded during vector store creation, retry with SentenceTransformer
            if "quota" in str(e).lower() or "429" in str(e):
                print(f"⚠️  OpenAI quota exceeded during initialization")
                print("🔄 Switching to local SentenceTransformer...")
                
                # Switch to SentenceTransformer
                self.embedder = embedders.SentenceTransformerEmbedder(
                    model="sentence-transformers/all-MiniLM-L6-v2"
                )
                
                # Retry vector store creation
                self.vector_server = vector_store.VectorStoreServer(
                    documents,
                    embedder=self.embedder,
                )
                print("✅ Vector store initialized with SentenceTransformer")
                return self.vector_server
            else:
                raise
    
    def run(self):
        """
        Run the Pathway server
        """
        # Setup vector store if not already done
        if not self.vector_server:
            self.setup_vector_store()
        
        print(f"🚀 Starting Pathway server on {config.HOST}:{config.PORT}")
        print(f"📍 API endpoint: http://{config.HOST}:{config.PORT}/v1/retrieve")
        print(f"💡 Test with: curl -X POST http://localhost:{config.PORT}/v1/retrieve -H 'Content-Type: application/json' -d '{{\"query\":\"test\",\"k\":3}}'")
        print()
        
        # Run the server with caching
        self.vector_server.run_server(
            host=config.HOST,
            port=config.PORT,
            with_cache=True,
            cache_backend=pw.persistence.Backend.filesystem(
                str(config.VECTOR_DB_PATH)
            )
        )


def main():
    """Main entry point"""
    print("="*60)
    print("Pathway Vector Indexer")
    print("="*60)
    print()
    
    try:
        indexer = SimpleVectorIndexer()
        indexer.run()
    except KeyboardInterrupt:
        print("\n👋 Shutting down Pathway server...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()