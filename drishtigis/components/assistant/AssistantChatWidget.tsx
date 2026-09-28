"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Bot,
  Sparkles,
  Send,
  X,
  Minimize2,
  Maximize2,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Layers,
  MapPin,
  ShieldCheck,
  Download,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Info
} from "lucide-react";
import { sendAssistantQuery } from "@/lib/api/assistant";
import { AssistantChatResponse, MapAction, ToolCallLog, ProvenanceInfo } from "@/lib/types/assistant";
import { useAuth } from "@/lib/auth/Context";

export interface AssistantChatWidgetProps {
  isOpen: boolean;
  onClose: () => void;
  hasSidebar?: boolean;
  selectedContext?: {
    entity_type?: "parcel" | "building" | "review" | "region";
    entity_id?: string;
    region_id?: string;
    dataset_id?: string;
  } | null;
  onExecuteMapAction?: (action: MapAction) => void;
}

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  toolCalls?: ToolCallLog[];
  provenance?: ProvenanceInfo;
  mapActions?: MapAction[];
}

export function AssistantChatWidget({
  isOpen,
  onClose,
  hasSidebar = false,
  selectedContext,
  onExecuteMapAction,
}: AssistantChatWidgetProps) {
  const { token, user } = useAuth();
  const [conversationId, setConversationId] = useState<string>("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const initialGreeting = `Hello! I am your **DrishtiGIS Spatial Intelligence Assistant** (SIH26012). 

I can explain the project mission, deep learning AI architecture (U-Net + ResNet18), Bhopal UAV orthomosaic coverage (5cm GSD), boundary discrepancy detection, or analyze any cadastral parcel on the map.`;

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      sender: "assistant",
      text: initialGreeting,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen && !isMinimized) {
      scrollToBottom();
    }
  }, [messages, isOpen, isMinimized]);

  const toggleTools = (msgId: string) => {
    setExpandedTools((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const handleSend = async (queryText?: string) => {
    const q = (queryText || input).trim();
    if (!q || loading) return;

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      sender: "user",
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInput("");
    setLoading(true);

    try {
      const activeEntityId = selectedContext?.entity_id;
      const resp: AssistantChatResponse = await sendAssistantQuery(
        {
          query: q,
          conversation_id: conversationId || undefined,
          context_entity: {
            entity_type: selectedContext?.entity_type || (activeEntityId ? "parcel" : "region"),
            entity_id: activeEntityId,
            region_id: selectedContext?.region_id || "bhopal_mp",
            dataset_id: selectedContext?.dataset_id || "uavpal_bhopal",
          },
        },
        token
      );

      if (resp.conversation_id && !conversationId) {
        setConversationId(resp.conversation_id);
      }

      const botMsg: ChatMessage = {
        id: `bot_${Date.now()}`,
        sender: "assistant",
        text: resp.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        toolCalls: resp.tool_calls,
        provenance: resp.provenance,
        mapActions: resp.map_actions,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      let errText = "The requested DrishtiGIS spatial tool could not be completed. Please check your backend connection.";
      if (err?.status === 401) {
        errText = "Authentication required. Your session may have expired. Please sign in again to use the AI assistant.";
      }
      const errMsg: ChatMessage = {
        id: `err_${Date.now()}`,
        sender: "assistant",
        text: errText,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const currentParcelId = selectedContext?.entity_type === "parcel" ? selectedContext.entity_id : undefined;

  return (
    <div
      className={`fixed z-50 transition-all duration-300 ease-in-out font-sans ${
        hasSidebar ? "bottom-5 right-5 sm:right-[435px]" : "bottom-5 right-5"
      } ${
        isMinimized
          ? "w-80 h-14"
          : "w-96 sm:w-[430px] h-[580px] max-h-[85vh]"
      } flex flex-col bg-[#FDFBF7] border border-[#E8E0D0] rounded-2xl shadow-2xl overflow-hidden`}
    >
      {/* ── Widget Header ─────────────────────────────────────────────── */}
      <div className="bg-[#2D5016] text-[#FBF9F5] px-4 py-3 flex items-center justify-between select-none shadow-md shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#3A6B1E] flex items-center justify-center relative shadow-xs">
            <Sparkles className="w-4 h-4 text-[#F7F3EC]" />
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-[#10B981] border-2 border-[#2D5016]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-xs tracking-tight">DrishtiGIS AI Assistant</span>
              <span className="text-[9px] bg-[#3A6B1E] text-white px-1.5 py-0.2 rounded font-mono font-semibold">
                SIH26012
              </span>
            </div>
            <p className="text-[10px] text-[#EDE8DE] opacity-90 truncate max-w-[200px]">
              {currentParcelId ? `Context: Parcel ${currentParcelId}` : "Grounded Spatial Intelligence"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 text-[#EDE8DE]">
          {/* Full Screen Link to dedicated page */}
          <Link
            href={
              currentParcelId
                ? `/app/assistant?entity_type=parcel&entity_id=${currentParcelId}`
                : `/app/assistant`
            }
            target="_blank"
            className="p-1 hover:text-white hover:bg-[#3A6B1E] rounded-md transition-colors"
            title="Open Dedicated Fullscreen Assistant"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </Link>

          {/* Minimize / Expand Toggle */}
          <button
            onClick={() => setIsMinimized((prev) => !prev)}
            className="p-1 hover:text-white hover:bg-[#3A6B1E] rounded-md transition-colors"
            title={isMinimized ? "Expand Chat" : "Minimize Chat"}
          >
            {isMinimized ? <ChevronUp className="w-4 h-4" /> : <Minimize2 className="w-3.5 h-3.5" />}
          </button>

          {/* Close Widget */}
          <button
            onClick={onClose}
            className="p-1 hover:text-white hover:bg-[#8C2D19] rounded-md transition-colors"
            title="Close Assistant"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* ── Context Notification Pill (If parcel selected) ─────────── */}
          {currentParcelId && (
            <div className="bg-[#2D5016]/10 border-b border-[#2D5016]/20 px-3.5 py-1.5 flex items-center justify-between text-[11px] text-[#2D5016] shrink-0">
              <div className="flex items-center gap-1.5 font-medium truncate">
                <MapPin className="w-3.5 h-3.5 shrink-0" />
                <span>Active Map Selection:</span>
                <span className="font-mono font-bold">{currentParcelId}</span>
              </div>
              <button
                onClick={() => handleSend(`Summarize parcel ${currentParcelId}`)}
                className="text-[10px] underline font-semibold hover:text-[#3A6B1E] shrink-0"
              >
                Summarize
              </button>
            </div>
          )}

          {/* ── Chat Messages Container ───────────────────────────────── */}
          <div className="flex-1 p-3.5 overflow-y-auto space-y-3.5 text-xs bg-[#F7F3EC]/50">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-2.5 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.sender === "assistant" && (
                  <div className="w-6 h-6 rounded-md bg-[#2D5016] text-[#FBF9F5] flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                    <Bot className="w-3.5 h-3.5" />
                  </div>
                )}

                <div
                  className={`max-w-[84%] rounded-xl p-3 space-y-2 shadow-xs ${
                    msg.sender === "user"
                      ? "bg-[#2D5016] text-[#FBF9F5] rounded-tr-none font-medium"
                      : "bg-[#FBF9F5] border border-[#E8E0D0] text-[#2C2C2C] rounded-tl-none"
                  }`}
                >
                  {/* Message Text with simple formatting */}
                  <div className="text-[11.5px] leading-relaxed whitespace-pre-wrap font-sans">
                    {msg.text.split("\n").map((line, lIdx) => {
                      if (line.startsWith("• ") || line.startsWith("- ")) {
                        return (
                          <div key={lIdx} className="flex items-start gap-1.5 my-0.5">
                            <span className="text-[#2D5016] font-bold">•</span>
                            <span>{line.replace(/^[•-]\s+/, "")}</span>
                          </div>
                        );
                      }
                      if (line.startsWith("**") && line.endsWith("**")) {
                        return (
                          <p key={lIdx} className="font-bold text-[#2D5016] text-[12px] my-1">
                            {line.replace(/\*\*/g, "")}
                          </p>
                        );
                      }
                      return (
                        <p key={lIdx} className={line.trim() === "" ? "h-2" : "my-0.5"}>
                          {line}
                        </p>
                      );
                    })}
                  </div>

                  {/* Provenance Badge */}
                  {msg.provenance && (
                    <div className="pt-1.5 border-t border-[#E8E0D0]/80 flex flex-wrap items-center gap-1.5 text-[9.5px]">
                      <span className="bg-[#2D5016]/10 text-[#2D5016] px-1.5 py-0.5 rounded font-mono font-semibold">
                        {msg.provenance.source_type}
                      </span>
                      {msg.provenance.model && (
                        <span className="bg-[#EDE8DE] text-[#2C2C2C] px-1.5 py-0.5 rounded font-medium">
                          {msg.provenance.model}
                        </span>
                      )}
                      {msg.provenance.disclaimer && (
                        <p className="w-full text-[#8C2D19] italic font-medium mt-0.5">
                          ⚠️ {msg.provenance.disclaimer}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Tool Calls Disclosure Accordion */}
                  {msg.toolCalls && msg.toolCalls.length > 0 && (
                    <div className="pt-1 border-t border-[#E8E0D0]/60">
                      <button
                        onClick={() => toggleTools(msg.id)}
                        className="flex items-center gap-1 text-[10px] text-[#8A8A8A] hover:text-[#2D5016] transition-colors"
                      >
                        <Info className="w-3 h-3" />
                        <span>Grounded via {msg.toolCalls.length} GIS Tool{msg.toolCalls.length > 1 ? "s" : ""}</span>
                        {expandedTools[msg.id] ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      </button>
                      {expandedTools[msg.id] && (
                        <div className="mt-1.5 bg-[#EDE8DE]/70 p-2 rounded-lg font-mono text-[9px] text-[#2C2C2C] space-y-1">
                          {msg.toolCalls.map((tc, tcIdx) => (
                            <div key={tcIdx} className="border-b border-[#E8E0D0] pb-1 last:border-b-0 last:pb-0">
                              <span className="font-bold text-[#2D5016]">tool: {tc.tool_name}</span>
                              <pre className="overflow-x-auto whitespace-pre-wrap max-h-24">
                                {JSON.stringify(tc.result, null, 2)}
                              </pre>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Interactive Map Actions */}
                  {msg.mapActions && msg.mapActions.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1.5 border-t border-[#E8E0D0]/80">
                      {msg.mapActions.map((ma, maIdx) => {
                        const isNav = ma.action === "OPEN_REVIEW" || ma.action === "OPEN_EXPORT";
                        const label =
                          ma.action === "SHOW_LAYER"
                            ? `Show ${ma.target_id || "Layer"}`
                            : ma.action === "ZOOM_TO_FEATURE"
                            ? `Zoom to ${ma.target_id || "Feature"}`
                            : ma.action === "SELECT_FEATURE"
                            ? `Select ${ma.target_id || "Feature"}`
                            : ma.action === "OPEN_REVIEW"
                            ? "Review Queue"
                            : "Export Center";

                        if (isNav) {
                          return (
                            <Link
                              key={maIdx}
                              href={ma.action === "OPEN_REVIEW" ? "/app/review" : "/app/exports"}
                              className="inline-flex items-center gap-1 bg-[#2D5016] text-[#FBF9F5] hover:bg-[#3A6B1E] px-2 py-0.5 rounded text-[10px] font-semibold transition-colors"
                            >
                              {ma.action === "OPEN_REVIEW" ? <ShieldCheck className="w-3 h-3" /> : <Download className="w-3 h-3" />}
                              <span>{label}</span>
                            </Link>
                          );
                        }

                        return (
                          <button
                            key={maIdx}
                            onClick={() => {
                              if (onExecuteMapAction) onExecuteMapAction(ma);
                            }}
                            className="inline-flex items-center gap-1 bg-[#2D5016] text-[#FBF9F5] hover:bg-[#3A6B1E] px-2 py-0.5 rounded text-[10px] font-semibold transition-colors shadow-2xs"
                          >
                            <MapPin className="w-3 h-3" />
                            <span>{label}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}

                  <span className="text-[9px] opacity-60 block text-right">
                    {msg.timestamp}
                  </span>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-2 items-center text-xs text-[#8A8A8A] bg-[#FBF9F5] border border-[#E8E0D0] p-2.5 rounded-xl shadow-2xs">
                <span className="w-2 h-2 rounded-full bg-[#2D5016] animate-ping" />
                <span>Running Grounded Spatial Engine & GIS Analysis...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* ── Quick Prompt Chips ────────────────────────────────────── */}
          <div className="bg-[#FBF9F5] border-t border-[#E8E0D0] p-2 overflow-x-auto shrink-0">
            <div className="flex items-center gap-1.5 whitespace-nowrap">
              <button
                onClick={() => handleSend("What is DrishtiGIS and what is problem statement SIH26012?")}
                className="bg-[#2D5016]/10 hover:bg-[#2D5016]/20 border border-[#2D5016]/30 text-[#2D5016] text-[10px] px-2.5 py-1 rounded-full font-semibold transition-colors"
              >
                🛰️ What is DrishtiGIS?
              </button>
              <button
                onClick={() => handleSend("What AI model is used for building footprint extraction?")}
                className="bg-[#7C3AED]/10 hover:bg-[#7C3AED]/20 border border-[#7C3AED]/30 text-[#7C3AED] text-[10px] px-2.5 py-1 rounded-full font-semibold transition-colors"
              >
                🧠 AI Model (U-Net)?
              </button>
              <button
                onClick={() => handleSend("What datasets and layers are available in Bhopal?")}
                className="bg-[#EDE8DE] hover:bg-[#E8E0D0] border border-[#E8E0D0] text-[#2C2C2C] text-[10px] px-2.5 py-1 rounded-full font-medium transition-colors"
              >
                🗺️ Bhopal Datasets
              </button>
              <button
                onClick={() => handleSend("What spatial discrepancies are flagged in Bhopal?")}
                className="bg-[#EDE8DE] hover:bg-[#E8E0D0] border border-[#E8E0D0] text-[#2C2C2C] text-[10px] px-2.5 py-1 rounded-full font-medium transition-colors"
              >
                ⚠️ Flagged Discrepancies
              </button>
              {currentParcelId && (
                <button
                  onClick={() => handleSend(`Why is parcel ${currentParcelId} under review?`)}
                  className="bg-[#C4922A]/10 hover:bg-[#C4922A]/20 border border-[#C4922A]/30 text-[#A67820] text-[10px] px-2.5 py-1 rounded-full font-semibold transition-colors"
                >
                  📋 Review {currentParcelId}
                </button>
              )}
            </div>
          </div>

          {/* ── Input Bar ─────────────────────────────────────────────── */}
          <div className="p-2.5 bg-[#FBF9F5] border-t border-[#E8E0D0] flex items-center gap-1.5 shrink-0">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={
                currentParcelId
                  ? `Ask about parcel ${currentParcelId} or the project...`
                  : "Ask about DrishtiGIS, AI models, datasets..."
              }
              className="flex-1 bg-[#FDFBF7] border border-[#E8E0D0] rounded-xl px-3 py-2 text-xs text-[#2C2C2C] placeholder-[#8A8A8A] focus:outline-none focus:border-[#2D5016] shadow-2xs"
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              className="bg-[#2D5016] hover:bg-[#3A6B1E] disabled:opacity-40 text-white p-2 rounded-xl transition-all shadow-xs flex items-center justify-center shrink-0"
              title="Send Message"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
