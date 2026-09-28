"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  Bot,
  Send,
  Sparkles,
  Building,
  Layers,
  AlertTriangle,
  MapPin,
  Compass,
  FileText,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Download
} from "lucide-react";
import { sendAssistantQuery } from "@/lib/api/assistant";
import { AssistantChatResponse, MapAction, ToolCallLog } from "@/lib/types/assistant";
import { useAuth } from "@/lib/auth/Context";

interface ChatMessageItem {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  toolCalls?: ToolCallLog[];
  provenance?: any;
  mapActions?: MapAction[];
}

function AssistantContent() {
  const { token, user } = useAuth();
  const searchParams = useSearchParams();
  const entityType = searchParams.get("entity_type") || "parcel";
  const entityId = searchParams.get("entity_id") || "DRS-BPL-DEMO-014";

  const [conversationId, setConversationId] = useState<string>("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showToolsMap, setShowToolsMap] = useState<Record<string, boolean>>({});

  const [messages, setMessages] = useState<ChatMessageItem[]>([
    {
      id: "welcome-1",
      sender: "assistant",
      text: `Hello! I am your DrishtiGIS Grounded Spatial Intelligence Assistant (SIH26012). I am grounded in live backend GIS tools, deep learning building segmentation (U-Net + ResNet18), UAV aerial orthomosaics (5cm GSD), OpenStreetMap reference infrastructure, and surveyor review queues.

You can ask me anything about the **DrishtiGIS platform**, our **AI architecture**, **Bhopal spatial datasets**, or inspect any cadastral parcel and discrepancy!`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const toggleTools = (msgId: string) => {
    setShowToolsMap((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg: ChatMessageItem = {
      id: Date.now().toString(),
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput("");
    setLoading(true);

    try {
      const resp: AssistantChatResponse = await sendAssistantQuery(
        {
          query,
          conversation_id: conversationId || undefined,
          context_entity: {
            entity_type: entityType as any,
            entity_id: entityId,
            region_id: "bhopal_mp",
            dataset_id: "uavpal_bhopal"
          }
        },
        token
      );

      if (resp.conversation_id && !conversationId) {
        setConversationId(resp.conversation_id);
      }

      const botMsg: ChatMessageItem = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: resp.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        toolCalls: resp.tool_calls,
        provenance: resp.provenance,
        mapActions: resp.map_actions
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      let errText = "The requested DrishtiGIS spatial tool could not be completed. Please check your backend connection.";
      if (err?.status === 401) {
        errText = "Authentication required. Your login session may have expired. Please sign in again to use the AI assistant.";
      }
      const errMsg: ChatMessageItem = {
        id: (Date.now() + 1).toString(),
        sender: "assistant",
        text: errText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F3EC] text-[#2C2C2C] flex flex-col font-sans">
      
      {/* Top Header */}
      <header className="bg-[#FBF9F5] border-b border-[#E8E0D0] px-4 lg:px-8 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/app/map" className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2D5016] hover:text-[#3A6B1E]">
            <ArrowLeft className="w-4 h-4" />
            <span>Return to WebGIS Map</span>
          </Link>
          <span className="text-[#8A8A8A]">/</span>
          <div className="flex items-center gap-1.5 font-display font-bold text-sm text-[#2C2C2C]">
            <Bot className="w-4 h-4 text-[#2D5016]" />
            <span>Grounded Spatial AI Assistant</span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-[#8A8A8A]">
          <span className="w-2 h-2 rounded-full bg-[#7D9154] animate-pulse" />
          <span>Context: {entityType.toUpperCase()} (<span className="font-mono font-bold text-[#2C2C2C]">{entityId}</span>)</span>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-4 lg:p-6 flex flex-col justify-between space-y-4">
        
        {/* Chat Thread */}
        <div className="flex-1 bg-[#FBF9F5] border border-[#E8E0D0] rounded-2xl p-4 lg:p-6 shadow-panel overflow-y-auto space-y-4 min-h-[480px]">
          
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 text-xs ${
                msg.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.sender === "assistant" && (
                <div className="w-7 h-7 rounded-lg bg-[#2D5016] text-[#FBF9F5] flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-xl rounded-xl p-4 space-y-3 ${
                  msg.sender === "user"
                    ? "bg-[#2D5016] text-[#FBF9F5] rounded-tr-none"
                    : "bg-[#F7F3EC] border border-[#E8E0D0] text-[#2C2C2C] rounded-tl-none"
                }`}
              >
                {/* Main Text Output */}
                <div className="leading-relaxed whitespace-pre-wrap">{msg.text}</div>

                {/* Collapsible Tool Activity Section */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="bg-[#FBF9F5] border border-[#E8E0D0] rounded-lg p-2.5 space-y-2">
                    <button
                      onClick={() => toggleTools(msg.id)}
                      className="flex items-center justify-between w-full text-[11px] font-semibold text-[#5A5A5A] hover:text-[#2C2C2C]"
                    >
                      <span className="flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-[#2D5016]" />
                        <span>GIS Tools Executed ({msg.toolCalls.length})</span>
                      </span>
                      {showToolsMap[msg.id] ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>

                    {showToolsMap[msg.id] && (
                      <div className="space-y-1.5 pt-1 border-t border-[#E8E0D0] text-[10px]">
                        {msg.toolCalls.map((tc, idx) => (
                          <div key={idx} className="bg-[#F7F3EC] p-2 rounded border border-[#E8E0D0] font-mono">
                            <span className="font-bold text-[#2D5016]">tool: {tc.tool_name}</span>
                            <pre className="mt-1 text-[9px] text-[#5A5A5A] overflow-x-auto">
                              {JSON.stringify(tc.result, null, 2)}
                            </pre>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Evidence / Source Chips */}
                {msg.provenance && (
                  <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                    <span className="bg-[#2D5016]/10 text-[#2D5016] border border-[#2D5016]/20 px-2 py-0.5 rounded font-mono font-bold">
                      {msg.provenance.source_type}
                    </span>
                    {msg.provenance.model && (
                      <span className="bg-[#E8E0D0] text-[#2C2C2C] px-2 py-0.5 rounded">
                        Model: {msg.provenance.model}
                      </span>
                    )}
                    {msg.provenance.confidence !== undefined && msg.provenance.confidence !== null && (
                      <span className="bg-[#E8E0D0] text-[#2C2C2C] px-2 py-0.5 rounded">
                        Confidence: {(msg.provenance.confidence * 100).toFixed(1)}%
                      </span>
                    )}
                    {msg.provenance.disclaimer && (
                      <span className="w-full text-[#8C2D19] font-medium mt-1">
                        ⚠️ {msg.provenance.disclaimer}
                      </span>
                    )}
                  </div>
                )}

                {/* Map UI Action Buttons */}
                {msg.mapActions && msg.mapActions.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-2 border-t border-[#E8E0D0]">
                    {msg.mapActions.map((ma, idx) => (
                      <Link
                        key={idx}
                        href={
                          ma.action === "OPEN_REVIEW"
                            ? "/app/review"
                            : ma.action === "OPEN_EXPORT"
                            ? "/app/exports"
                            : `/app/map?selected=${ma.target_id || entityId}`
                        }
                        className="inline-flex items-center gap-1 bg-[#2D5016] text-[#FBF9F5] hover:bg-[#3A6B1E] px-2.5 py-1 rounded text-[11px] font-medium transition-colors"
                      >
                        {ma.action === "OPEN_REVIEW" ? (
                          <>
                            <ShieldCheck className="w-3 h-3" />
                            <span>Open Review Queue</span>
                          </>
                        ) : ma.action === "OPEN_EXPORT" ? (
                          <>
                            <Download className="w-3 h-3" />
                            <span>Export Center</span>
                          </>
                        ) : (
                          <>
                            <MapPin className="w-3 h-3" />
                            <span>View on Map ({ma.target_id || entityId})</span>
                          </>
                        )}
                      </Link>
                    ))}
                  </div>
                )}

                <span className="text-[9px] opacity-60 block text-right">
                  {msg.timestamp}
                </span>
              </div>

              {msg.sender === "user" && (
                <div className="w-7 h-7 rounded-lg bg-[#EDE8DE] text-[#2C2C2C] flex items-center justify-center shrink-0 font-bold">
                  You
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-2 items-center text-xs text-[#8A8A8A] p-2">
              <span className="w-2 h-2 rounded-full bg-[#2D5016] animate-ping" />
              <span>Executing DrishtiGIS GIS Tools & Grounding Analysis...</span>
            </div>
          )}

        </div>

        {/* Query Suggestion Pills */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-[#8A8A8A] font-semibold">
            <Sparkles className="w-3 h-3 text-[#C4922A]" />
            <span>Suggested Questions:</span>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <button
              onClick={() => handleSend("What is DrishtiGIS and what is problem statement SIH26012?")}
              className="bg-[#2D5016]/10 border border-[#2D5016]/30 hover:bg-[#2D5016]/20 px-3 py-1.5 rounded-full text-[#2D5016] text-[11px] font-semibold transition-colors flex items-center gap-1"
            >
              🛰️ What is DrishtiGIS (SIH26012)?
            </button>
            <button
              onClick={() => handleSend("What AI model is used for building footprint extraction?")}
              className="bg-[#7C3AED]/10 border border-[#7C3AED]/30 hover:bg-[#7C3AED]/20 px-3 py-1.5 rounded-full text-[#7C3AED] text-[11px] font-semibold transition-colors flex items-center gap-1"
            >
              🧠 U-Net + ResNet18 AI Model?
            </button>
            <button
              onClick={() => handleSend("What datasets and layers are available in Bhopal?")}
              className="bg-[#FBF9F5] border border-[#E8E0D0] hover:border-[#2D5016] px-3 py-1.5 rounded-full text-[#2C2C2C] text-[11px] font-medium transition-colors"
            >
              🗺️ Bhopal UAV Datasets & Layers?
            </button>
            <button
              onClick={() => handleSend("What spatial discrepancies are flagged in Bhopal?")}
              className="bg-[#FBF9F5] border border-[#E8E0D0] hover:border-[#2D5016] px-3 py-1.5 rounded-full text-[#2C2C2C] text-[11px] font-medium transition-colors"
            >
              ⚠️ Active Discrepancies & Overhangs?
            </button>
            <button
              onClick={() => handleSend(`Why is parcel ${entityId} under review?`)}
              className="bg-[#FBF9F5] border border-[#E8E0D0] hover:border-[#2D5016] px-3 py-1.5 rounded-full text-[#2C2C2C] text-[11px] font-medium transition-colors"
            >
              📋 Review Status for {entityId}?
            </button>
            <button
              onClick={() => handleSend(`How many buildings are inside parcel ${entityId}?`)}
              className="bg-[#FBF9F5] border border-[#E8E0D0] hover:border-[#2D5016] px-3 py-1.5 rounded-full text-[#2C2C2C] text-[11px] font-medium transition-colors"
            >
              🏢 Buildings inside {entityId}?
            </button>
            <button
              onClick={() => handleSend("How can I export GIS data?")}
              className="bg-[#FBF9F5] border border-[#E8E0D0] hover:border-[#2D5016] px-3 py-1.5 rounded-full text-[#2C2C2C] text-[11px] font-medium transition-colors"
            >
              📦 Export GIS Data?
            </button>
          </div>
        </div>

        {/* Input Bar */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleSend(); }}
            placeholder={`Ask grounded questions about parcel ${entityId}...`}
            className="flex-1 bg-[#FBF9F5] border border-[#E8E0D0] rounded-xl px-4 py-3 text-xs text-[#2C2C2C] placeholder-[#8A8A8A] focus:outline-none focus:border-[#2D5016]"
          />
          <button
            onClick={() => handleSend()}
            disabled={loading}
            className="bg-[#2D5016] hover:bg-[#3A6B1E] disabled:opacity-50 text-[#FBF9F5] px-4 py-3 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs"
          >
            <span>Send</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>

      </main>

    </div>
  );
}

export default function AssistantPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs">Loading DrishtiGIS Assistant...</div>}>
      <AssistantContent />
    </Suspense>
  );
}
