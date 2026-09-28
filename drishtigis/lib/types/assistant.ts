export interface ProvenanceInfo {
  source_type: string;
  dataset_id?: string;
  region_id?: string;
  feature_id?: string;
  model?: string;
  acquisition_datetime?: string;
  confidence?: number;
  disclaimer?: string;
}

export interface MapAction {
  action: "ZOOM_TO_FEATURE" | "SELECT_FEATURE" | "OPEN_REVIEW" | "SHOW_LAYER" | "OPEN_EXPORT";
  target_type?: string;
  target_id?: string;
  params?: Record<string, any>;
}

export interface ToolCallLog {
  tool_name: string;
  result: Record<string, any>;
}

export interface AssistantChatRequest {
  query: string;
  conversation_id?: string;
  context_entity?: {
    entity_type?: "parcel" | "building" | "review" | "region";
    entity_id?: string;
    region_id?: string;
    dataset_id?: string;
  };
}

export interface AssistantChatResponse {
  request_id: string;
  conversation_id: string;
  query: string;
  answer: string;
  tool_calls: ToolCallLog[];
  provenance?: ProvenanceInfo;
  map_actions?: MapAction[];
  mode: string;
}

export interface ToolSchemaItem {
  name: string;
  description: string;
  parameters: Array<{
    name: string;
    type: string;
    description: string;
    required: boolean;
  }>;
}
