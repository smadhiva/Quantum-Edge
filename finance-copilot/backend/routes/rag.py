from fastapi import APIRouter, Request, HTTPException
import httpx
import os

router = APIRouter()

VECTOR_INDEXER_URL = os.getenv("VECTOR_INDEXER_URL", "http://finance-copilot-vector-indexer:8000")

@router.post("/rag-search")
async def rag_search(request: Request):
    try:
        payload = await request.json()
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{VECTOR_INDEXER_URL}/v1/retrieve", json=payload)
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
