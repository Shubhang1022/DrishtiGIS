import { AssistantChatRequest, AssistantChatResponse, ToolSchemaItem } from "@/lib/types/assistant";
import { apiFetch } from "@/lib/api/client";

export async function sendAssistantQuery(req: AssistantChatRequest, token?: string | null): Promise<AssistantChatResponse> {
  return apiFetch<AssistantChatResponse>("/api/v1/assistant/chat", {
    method: "POST",
    body: JSON.stringify(req),
    token,
  });
}

export async function fetchAssistantTools(token?: string | null): Promise<{ tool_count: number; tools: ToolSchemaItem[] }> {
  return apiFetch<{ tool_count: number; tools: ToolSchemaItem[] }>("/api/v1/assistant/tools", {
    token,
  });
}
