"""
DrishtiGIS Assistant Service.
Handles conversation context, history persistence, tool execution logging, and orchestration.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from backend.app.assistant.llm_provider import llm_provider, AssistantResponse, MapAction

class ChatMessage(BaseModel):
    id: str
    conversation_id: str
    role: str  # "user" | "assistant"
    content: str
    timestamp: float
    tool_calls: Optional[List[Dict[str, Any]]] = None
    provenance: Optional[Dict[str, Any]] = None
    map_actions: Optional[List[Dict[str, Any]]] = None
    context_entity: Optional[Dict[str, Any]] = None

class ToolExecutionLog(BaseModel):
    request_id: str
    conversation_id: str
    timestamp: float
    tool_name: str
    inputs: Dict[str, Any]
    success: bool
    error: Optional[str] = None

class AssistantService:
    def __init__(self):
        self._conversations: Dict[str, List[ChatMessage]] = {}
        self._execution_logs: List[ToolExecutionLog] = []

    def handle_query(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        context_entity: Optional[Dict[str, Any]] = None,
        user: Optional[Any] = None
    ) -> Dict[str, Any]:
        cid = conversation_id or f"conv_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        now = time.time()

        if cid not in self._conversations:
            self._conversations[cid] = []

        # Store user message
        user_msg = ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            conversation_id=cid,
            role="user",
            content=query,
            timestamp=now,
            context_entity=context_entity
        )
        self._conversations[cid].append(user_msg)

        # Process query with LLMProvider / Grounded Tool Engine
        history_payload = [m.model_dump() for m in self._conversations[cid][-5:]]
        response: AssistantResponse = llm_provider.process_query(
            query=query,
            context_entity=context_entity,
            history=history_payload,
            user=user
        )

        # Log tool execution logs
        for tc in response.tool_calls:
            self._execution_logs.append(
                ToolExecutionLog(
                    request_id=request_id,
                    conversation_id=cid,
                    timestamp=now,
                    tool_name=tc.get("tool_name", "unknown"),
                    inputs=context_entity or {},
                    success=True
                )
            )

        # Build assistant message
        map_actions_list = [ma.model_dump() for ma in response.map_actions]
        assistant_msg = ChatMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            conversation_id=cid,
            role="assistant",
            content=response.text,
            timestamp=now,
            tool_calls=response.tool_calls,
            provenance=response.provenance,
            map_actions=map_actions_list,
            context_entity=context_entity
        )
        self._conversations[cid].append(assistant_msg)

        return {
            "request_id": request_id,
            "conversation_id": cid,
            "query": query,
            "answer": response.text,
            "tool_calls": response.tool_calls,
            "provenance": response.provenance,
            "map_actions": map_actions_list,
            "mode": response.mode
        }

    def get_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        messages = self._conversations.get(conversation_id, [])
        return [m.model_dump() for m in messages]

    def get_logs(self) -> List[Dict[str, Any]]:
        return [l.model_dump() for l in self._execution_logs[-50:]]

assistant_service = AssistantService()
