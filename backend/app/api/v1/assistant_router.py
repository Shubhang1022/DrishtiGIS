"""
DrishtiGIS Grounded Geospatial AI Assistant API Router.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.app.assistant.assistant_service import assistant_service
from backend.app.assistant.tool_registry import tool_registry
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.user_model import User

router = APIRouter()

class ChatQueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    context_entity: Optional[Dict[str, Any]] = None

@router.post("/chat", summary="Query the Grounded Geospatial AI Assistant")
async def chat_with_assistant(
    req: ChatQueryRequest,
    current_user: User = Depends(get_current_user)
):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
    
    result = assistant_service.handle_query(
        query=req.query,
        conversation_id=req.conversation_id,
        context_entity=req.context_entity,
        user=current_user
    )
    return result

@router.get("/tools", summary="List registered DrishtiGIS AI Assistant tools and schemas")
async def list_assistant_tools(current_user: User = Depends(get_current_user)):
    return {
        "tool_count": len(tool_registry._tools),
        "tools": tool_registry.get_schemas()
    }

@router.get("/history/{conversation_id}", summary="Get conversation history")
async def get_conversation_history(conversation_id: str, current_user: User = Depends(get_current_user)):
    messages = assistant_service.get_history(conversation_id)
    return {
        "conversation_id": conversation_id,
        "message_count": len(messages),
        "messages": messages
    }

@router.get("/logs", summary="Get recent AI Assistant tool execution logs")
async def get_tool_execution_logs(current_user: User = Depends(get_current_user)):
    return {
        "logs": assistant_service.get_logs()
    }
