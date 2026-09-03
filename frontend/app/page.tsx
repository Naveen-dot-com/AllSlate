"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import {
  Bot,
  ChevronRight,
  FileText,
  FolderOpen,
  LoaderCircle,
  MessageSquarePlus,
  PanelRightOpen,
  Plus,
  Search,
  Send,
  Settings2,
  Sparkles,
  Upload,
  X,
} from "lucide-react";
import { api, ask, DocumentDetail, DocumentItem, ElementItem, Message, Settings } from "@/lib/api";
import { ConfidenceBadge } from "@/components/documents/confidence-badge";
import { ThemeToggle } from "@/components/theme-toggle";
import { TiltCard } from "@/components/tilt-card";

const projectId = "demo";
const RESPONSE_STYLES = ["precise", "balanced", "creative"] as const;
const DOCUMENT_TYPES = ["text", "table", "image"] as const;

const defaultSettings: Settings = {
  web_search_enabled: false,
  creativity_level: "balanced",
  retrieval_top_k: 6,
  included_document_types: ["text", "table", "image"],
  updated_at: "",
};

export default function Workspace() {
  const [conversationId, setConversationId] = useState<string>();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<DocumentDetail>();
  const [elements, setElements] = useState<ElementItem[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [settings, setSettings] = useState(defaultSettings);
  const [settingsOpen, setSettingsOpen] = useState(true);
  const [question, setQuestion] = useState("");
  const [phase, setPhase] = useState("");
  const [error, setError] = useState("");

  const loadDocuments = () =>
    api
      .documents(projectId)
      .then(setDocuments)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load documents."));

  useEffect(() => {
    loadDocuments();
  }, []);

  async function openDocument(documentId: string) {
    try {
      const [detail, documentElements] = await Promise.all([
        api.document(projectId, documentId),
        api.elements(projectId, documentId),
      ]);
      setSelectedDocument(detail);
      setElements(documentElements);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to open document.");
    }
  }

  async function startConversation() {
    try {
      const conversation = await api.createConversation(projectId);
      setConversationId(conversation.id);
      setMessages([]);
      setSettings(await api.settings(projectId, conversation.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create a conversation.");
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!question.trim() || !conversationId) return;
    const content = question.trim();
    setQuestion("");
    setMessages((current) => [
      ...current,
      {
        id: `local-${Date.now()}`,
        sequence_number: current.length,
        role: "user",
        content,
        status: "complete",
        failure_reason: null,
        is_grounded: false,
        created_at: "",
        citations: [],
      },
    ]);
    setPhase("Retrieving sources");
    try {
      await ask(projectId, conversationId, content, (event, data) => {
        if (event === "phase") setPhase(data.phase === "generating" ? "Writing answer" : "Retrieving sources");
        if (event === "complete") {
          setMessages((current) => [
            ...current,
            {
              id: String(data.message_id),
              sequence_number: current.length,
              role: "assistant",
              content: String(data.content),
              status: "complete",
              failure_reason: null,
              is_grounded: Boolean(data.is_grounded),
              created_at: "",
              citations: (data.citations as Message["citations"]) ?? [],
            },
          ]);
          setPhase("");
        }
        if (event === "failed") {
          setError(String(data.failure_reason));
          setPhase("");
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to answer.");
      setPhase("");
    }
  }

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      await api.upload(projectId, file);
      loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      event.target.value = "";
    }
  }

  async function updateSettings(patch: Partial<Settings>) {
    if (!conversationId) return;
    try {
      setSettings(await api.updateSettings(projectId, conversationId, patch));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save settings.");
    }
  }

  function toggleDocumentType(type: string) {
    const types = settings.included_document_types.includes(type)
      ? settings.included_document_types.filter((item) => item !== type)
      : [...settings.included_document_types, type];
    if (types.length) updateSettings({ included_document_types: types });
  }

  return (
    <main className="workspace">
      <div className="orb orb-a" aria-hidden="true" />
      <div className="orb orb-b" aria-hidden="true" />
      <div className="orb orb-c" aria-hidden="true" />

      <aside className="rail glass">
        <div className="brand">
          <Sparkles size={18} /> AllSlate
        </div>
        <button className="project-switch">
          <span className="project-mark">D</span>
          <span>Demo workspace</span>
          <ChevronRight size={15} />
        </button>
        <nav>
          <button className="nav-active">
            <FolderOpen size={18} /> Workspace
          </button>
          <button>
            <Search size={18} /> Search
          </button>
        </nav>
        <div className="rail-bottom">
          <ThemeToggle />
          <button>
            <Settings2 size={18} /> Preferences
          </button>
          <div className="avatar">N</div>
        </div>
      </aside>

      <section className="documents glass">
        <header>
          <div>
            <p className="eyebrow">Project library</p>
            <h1>Documents</h1>
          </div>
          <label className="icon-button" title="Upload document">
            <Upload size={18} />
            <input type="file" onChange={upload} />
          </label>
        </header>
        <div className="document-list">
          {documents.map((document) => (
            <button
              key={document.id}
              onClick={() => openDocument(document.id)}
              className={selectedDocument?.id === document.id ? "document selected" : "document"}
            >
              <FileText size={18} />
              <span>
                <strong>{document.filename}</strong>
                <small>
                  {document.file_type.toUpperCase()} · {document.status.replace("_", " ")}
                </small>
              </span>
            </button>
          ))}
        </div>
        {selectedDocument && (
          <section className="inspection">
            <div className="inspection-heading">
              <div>
                <p className="eyebrow">Inspection</p>
                <h2>{selectedDocument.filename}</h2>
              </div>
              <button className="plain-button" onClick={() => setSelectedDocument(undefined)}>
                <X size={16} />
              </button>
            </div>
            {selectedDocument.has_low_confidence_content && (
              <div className="notice">Partial extraction: review marked elements before relying on them.</div>
            )}
            {selectedDocument.failure_category && (
              <div className="notice danger">{selectedDocument.failure_category.replaceAll("_", " ")}</div>
            )}
            <div className="element-list">
              {elements.map((element) => (
                <div className="element" key={element.id}>
                  <ConfidenceBadge level={element.confidence} />
                  <span>
                    {element.element_type} · page {element.page_number ?? "-"}
                  </span>
                  {element.confidence_reason && <small>{element.confidence_reason}</small>}
                </div>
              ))}
            </div>
          </section>
        )}
      </section>

      <section className="chat glass">
        <header>
          <div>
            <p className="eyebrow">Demo workspace</p>
            <h1>Ask your library</h1>
          </div>
          <button onClick={startConversation} className="new-chat">
            <MessageSquarePlus size={17} /> New chat
          </button>
        </header>
        {!conversationId ? (
          <TiltCard className="empty-chat">
            <div className="spark">
              <Bot size={26} />
            </div>
            <h2>Start with a question</h2>
            <p>AllSlate finds the relevant material in your project and keeps every answer tied to its source.</p>
            <button onClick={startConversation} className="primary">
              <Plus size={17} /> Start a conversation
            </button>
          </TiltCard>
        ) : (
          <>
            <div className="messages">
              {messages.map((message) => (
                <article key={message.id} className={`message ${message.role}`}>
                  <div className="message-label">
                    {message.role === "user" ? "You" : "AllSlate"}
                    {message.role === "assistant" && message.is_grounded ? <span>Grounded</span> : null}
                  </div>
                  <p>{message.content}</p>
                  {message.citations.length > 0 && (
                    <div className="citations">
                      {message.citations.map((citation, index) => (
                        <button onClick={() => openDocument(citation.document_id)} key={`${citation.document_id}-${index}`}>
                          <FileText size={14} />
                          {citation.document_id}
                          {citation.page_number ? ` · p.${citation.page_number}` : ""}
                        </button>
                      ))}
                    </div>
                  )}
                </article>
              ))}
              {phase && (
                <div className="phase">
                  <LoaderCircle size={16} />
                  {phase}
                </div>
              )}
            </div>
            <form onSubmit={submit} className="composer">
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask a question about your documents..."
                rows={2}
              />
              <button className="send" aria-label="Send question" disabled={!question.trim() || Boolean(phase)}>
                <Send size={18} />
              </button>
            </form>
          </>
        )}
      </section>

      <aside className={settingsOpen ? "settings-panel glass open" : "settings-panel glass"}>
        <button className="settings-toggle" title="Toggle settings" onClick={() => setSettingsOpen((value) => !value)}>
          <PanelRightOpen size={18} />
        </button>
        {settingsOpen && (
          <div className="settings-content">
            <p className="eyebrow">Conversation</p>
            <h2>Answer settings</h2>
            <label className="switch-row">
              <span>
                <strong>Web search</strong>
                <small>Use current web sources when useful</small>
              </span>
              <input
                type="checkbox"
                checked={settings.web_search_enabled}
                disabled={!conversationId}
                onChange={(event) => updateSettings({ web_search_enabled: event.target.checked })}
              />
            </label>
            <fieldset disabled={!conversationId}>
              <legend>Response style</legend>
              <div className="segmented">
                {RESPONSE_STYLES.map((level) => (
                  <button
                    type="button"
                    onClick={() => updateSettings({ creativity_level: level })}
                    className={settings.creativity_level === level ? "active" : ""}
                    key={level}
                  >
                    {level}
                  </button>
                ))}
              </div>
            </fieldset>
            <label className="range-label">
              Sources per answer <strong>{settings.retrieval_top_k}</strong>
              <input
                type="range"
                min="1"
                max="20"
                value={settings.retrieval_top_k}
                disabled={!conversationId}
                onChange={(event) => updateSettings({ retrieval_top_k: Number(event.target.value) })}
              />
            </label>
            <fieldset disabled={!conversationId}>
              <legend>Include document types</legend>
              {DOCUMENT_TYPES.map((type) => (
                <label className="check-row" key={type}>
                  <input
                    type="checkbox"
                    checked={settings.included_document_types.includes(type)}
                    onChange={() => toggleDocumentType(type)}
                  />
                  {type}
                </label>
              ))}
            </fieldset>
          </div>
        )}
      </aside>

      {error && (
        <div role="alert" className="toast">
          {error}
          <button onClick={() => setError("")}>
            <X size={15} />
          </button>
        </div>
      )}
    </main>
  );
}