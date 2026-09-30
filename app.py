"""
Run with: python -m uvicorn app:app --reload
Then test at http://127.0.0.1:8000/docs (auto-generated interactive API docs)
"""
from fastapi import FastAPI, HTTPException
from database.schemas import ChatMessage, ChatResponse
from core.agent import handle_message
from knowledge.tools import check_complaint_status
from database.database import init_db

app = FastAPI(title="AppInSnap Support Agent")

init_db()  # ensure tables exist on startup


@app.get("/")
def root():
    return {"status": "ok", "service": "AppInSnap support agent"}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatMessage):
    """Main conversational endpoint -- goes through the LLM + tools."""
    result = handle_message(
        session_id=payload.session_id,
        user_id=payload.user_id,
        message=payload.message,
    )
    return ChatResponse(reply=result["reply"], tool_used=result["tool_used"])


@app.get("/complaint/{complaint_number}")
def get_complaint(complaint_number: str):
    """Direct status check, bypassing the LLM for speed."""
    result = check_complaint_status(complaint_number)
    if not result["found"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result