import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import create_document, get_documents, db
from schemas import KnowledgeItem

app = FastAPI(title="Chat Knowledge Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Chat Knowledge Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_ID") or os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Knowledge Library Endpoints

class KnowledgeCreate(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = None
    source: Optional[str] = None

@app.post("/api/knowledge")
def add_knowledge(item: KnowledgeCreate):
    try:
        # validate with schema and insert
        model = KnowledgeItem(**item.model_dump())
        inserted_id = create_document("knowledgeitem", model)
        return {"id": inserted_id, "message": "Knowledge added"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/knowledge")
def list_knowledge(tag: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    filter_dict = {}
    if tag:
        filter_dict["tags"] = {"$in": [tag]}
    if q:
        filter_dict["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"content": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}},
        ]
    docs = get_documents("knowledgeitem", filter_dict, limit)
    # ensure ids are strings
    for d in docs:
        if isinstance(d.get("_id"), ObjectId):
            d["id"] = str(d.pop("_id"))
    return {"items": docs}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
