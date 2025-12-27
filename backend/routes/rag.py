from fastapi import APIRouter, Request, HTTPException, UploadFile, File
import httpx
import os
import logging
import shutil
from typing import Optional

router = APIRouter()

VECTOR_INDEXER_URL = os.getenv("VECTOR_INDEXER_URL", "http://localhost:8001")
DOCS_PATH = os.getenv("DOCS_PATH", "./data/documents")

# Ensure docs directory exists
os.makedirs(DOCS_PATH, exist_ok=True)

@router.post("/rag-search")
async def rag_search(request: Request):
    """Search indexed documents using RAG"""
    try:
        # Read raw body and validate it's JSON
        body = await request.body()
        if not body:
            logging.warning("Empty request body received on /rag-search")
            raise HTTPException(status_code=400, detail="Empty request body. Expected JSON payload.")

        import json as _json
        try:
            payload = _json.loads(body)
        except _json.JSONDecodeError as e:
            snippet = body.decode(errors="replace")[:200]
            logging.warning("Invalid JSON payload received on /rag-search: %s", snippet)
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e.msg}")

        # Validate required fields
        if "query" not in payload:
            raise HTTPException(status_code=400, detail="Missing required field: 'query'")

        # Try configured URL first, then fallback to localhost:8001
        urls_to_try = [VECTOR_INDEXER_URL]
        localhost_fallback = "http://localhost:8001"
        if localhost_fallback not in urls_to_try:
            urls_to_try.append(localhost_fallback)

        async with httpx.AsyncClient() as client:
            last_exc = None
            for base in urls_to_try:
                try:
                    resp = await client.post(f"{base}/v1/retrieve", json=payload, timeout=15.0)
                    resp.raise_for_status()
                    try:
                        return resp.json()
                    except ValueError:
                        logging.error("Non-JSON response from %s: %s", base, resp.text[:200])
                        raise HTTPException(status_code=502, detail=f"Upstream returned non-JSON response from {base}")
                except httpx.HTTPStatusError as e:
                    status = e.response.status_code if e.response is not None else 'unknown'
                    text = e.response.text[:200] if e.response is not None else ''
                    logging.error("Upstream error from %s: %s %s", base, status, text)
                    raise HTTPException(status_code=502, detail=f"Upstream returned {status} from {base}: {text}")
                except Exception as e:
                    logging.warning("Could not reach vector indexer at %s: %s", base, e)
                    last_exc = e
                    continue

        logging.exception("All attempts failed to contact vector indexer")
        raise HTTPException(status_code=502, detail=f"Failed to contact vector indexer: {last_exc}")

    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Unexpected error in rag_search: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag-health")
async def rag_health():
    """Health-check for the vector indexer"""
    urls_to_try = [VECTOR_INDEXER_URL, "http://localhost:8001"]
    tried = []
    
    async with httpx.AsyncClient() as client:
        for base in urls_to_try:
            tried.append(base)
            try:
                # Try a simple retrieve query instead of statistics
                resp = await client.post(
                    f"{base}/v1/retrieve",
                    json={"query": "test", "k": 1},
                    timeout=5.0
                )
                resp.raise_for_status()
                return {
                    "vector_indexer": base,
                    "status": "ok",
                    "message": "Vector store is responding"
                }
            except Exception as e:
                logging.warning("Health probe failed for %s: %s", base, e)
                continue

    logging.error("Vector indexer unreachable on hosts: %s", ", ".join(tried))
    raise HTTPException(
        status_code=502,
        detail=f"Vector indexer unreachable. Tried: {', '.join(tried)}"
    )


@router.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document to be indexed by the vector store
    
    The document will be saved to the documents directory and
    automatically indexed by the Pathway streaming pipeline.
    """
    try:
        # Validate file extension
        allowed_extensions = [".pdf", ".txt", ".md", ".docx", ".csv", ".json"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed: {allowed_extensions}"
            )
        
        # Save file to documents directory
        file_path = os.path.join(DOCS_PATH, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        
        logging.info(f"Document uploaded: {file.filename} ({file_size} bytes)")
        
        return {
            "message": "Document uploaded successfully",
            "filename": file.filename,
            "size": file_size,
            "path": file_path,
            "status": "indexing (may take a few moments)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Error uploading document: %s", e)
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


@router.get("/documents")
async def list_documents():
    """List all documents in the index"""
    try:
        if not os.path.exists(DOCS_PATH):
            return {"documents": [], "count": 0}
        
        documents = []
        for filename in os.listdir(DOCS_PATH):
            file_path = os.path.join(DOCS_PATH, filename)
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                documents.append({
                    "filename": filename,
                    "size": file_stat.st_size,
                    "modified": file_stat.st_mtime,
                    "extension": os.path.splitext(filename)[1]
                })
        
        return {
            "documents": documents,
            "count": len(documents),
            "path": DOCS_PATH
        }
        
    except Exception as e:
        logging.exception("Error listing documents: %s", e)
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document from the index"""
    try:
        # Prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        file_path = os.path.join(DOCS_PATH, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document not found")
        
        os.remove(file_path)
        logging.info(f"Document deleted: {filename}")
        
        return {
            "message": "Document deleted successfully",
            "filename": filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Error deleting document: %s", e)
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")