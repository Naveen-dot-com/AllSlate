"use client";

import { ChangeEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  Bot,
  Check,
  ChevronRight,
  FileText,
  LoaderCircle,
  MessageSquarePlus,
  PanelRightOpen,
  Pencil,
  Plus,
  Send,
  Settings2,
  Sparkles,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { api, ask, DocumentDetail, DocumentItem, ElementItem, Message, Settings } from "@/lib/api";
import { ConfidenceBadge } from "@/components/documents/confidence-badge";
import { ThemeToggle } from "@/components/theme-toggle";
import { TiltCard } from "@/components/tilt-card";

type Workspace = {
  id: string;
  name: string;
  projectId: string;
  documents: DocumentItem[];
  conversationId?: string;
  settings: Settings;
  messages: Message[];
};

const WORKSPACE_STORAGE_KEY = "allslate-workspaces-v1";
const RESPONSE_STYLES = ["precise", "balanced", "creative"] as const;
const DOCUMENT_TYPES = ["text", "table", "image"] as const;

const defaultSettings: Settings = {
  web_search_enabled: false,
  creativity_level: "balanced",
  retrieval_top_k: 6,
  included_document_types: ["text", "table", "image"],
  updated_at: "",
};

function buildWorkspace(name: string, id: string): Workspace {
  return {
    id,
    name,
    projectId: id,
    documents: [],
    settings: { ...defaultSettings },
    messages: [],
  };
}

const FALLBACK_WORKSPACES: Workspace[] = [
  buildWorkspace("Workspace 1", "workspace-1"),
  buildWorkspace("Workspace 2", "workspace-2"),
];

function readStoredWorkspaces(): Workspace[] {
  if (typeof window === "undefined") {
    return FALLBACK_WORKSPACES;
  }

  try {
    const raw = window.localStorage.getItem(WORKSPACE_STORAGE_KEY);
    if (!raw) {
      return FALLBACK_WORKSPACES;
    }

    const parsed = JSON.parse(raw) as Workspace[];
    if (Array.isArray(parsed) && parsed.length > 0) {
      return parsed.map((workspace) => ({
        ...workspace,
        settings: { ...defaultSettings, ...workspace.settings },
        documents: workspace.documents ?? [],
        messages: workspace.messages ?? [],
      }));
    }
  } catch {
    // Ignore and rebuild if storage is unavailable or invalid.
  }

  return FALLBACK_WORKSPACES;
}

function getProgressForStatus(status: string | undefined): { progress: number; etaSeconds: number } {
  switch (status) {
    case "queued":
      return { progress: 10, etaSeconds: 45 };
    case "partitioning":
      return { progress: 38, etaSeconds: 31 };
    case "chunking":
      return { progress: 60, etaSeconds: 21 };
    case "summarizing":
      return { progress: 76, etaSeconds: 12 };
    case "vectorizing":
      return { progress: 90, etaSeconds: 5 };
    case "stored":
    case "stored_partial":
    case "failed":
      return { progress: 100, etaSeconds: 0 };
    default:
      return { progress: 0, etaSeconds: 0 };
  }
}

export default function Workspace() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>(() => FALLBACK_WORKSPACES);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string>("workspace-1");
  const [selectedDocument, setSelectedDocument] = useState<DocumentDetail>();
  const [elements, setElements] = useState<ElementItem[]>([]);
  const [settingsOpen, setSettingsOpen] = useState(true);
  const [settingsPanelWidth, setSettingsPanelWidth] = useState(330);
  const [railWidth, setRailWidth] = useState(240);
  const [documentsWidth, setDocumentsWidth] = useState(340);
  const resizeStartRef = useRef<{ type: "rail" | "documents" | "settings"; startX: number; startWidth: number } | null>(null);
  const [question, setQuestion] = useState("");
  const [phase, setPhase] = useState("");
  const [error, setError] = useState("");
  const [progressByDocument, setProgressByDocument] = useState<Record<string, number>>({});
  const [editingWorkspaceId, setEditingWorkspaceId] = useState<string | null>(null);
  const [workspaceDraftName, setWorkspaceDraftName] = useState("");
  const [expandedWorkspaceId, setExpandedWorkspaceId] = useState<string | null>(null);

  const activeWorkspace = useMemo(
    () => workspaces.find((workspace) => workspace.id === activeWorkspaceId) ?? workspaces[0],
    [activeWorkspaceId, workspaces],
  );

  const projectId = activeWorkspace?.projectId ?? "workspace-1";
  const conversationId = activeWorkspace?.conversationId;
  const settings = activeWorkspace?.settings ?? defaultSettings;
  const messages = activeWorkspace?.messages ?? [];

  useEffect(() => {
    const stored = readStoredWorkspaces();
    if (stored.length > 0) {
      setWorkspaces(stored);
      setActiveWorkspaceId((currentId) => currentId || stored[0]?.id || "workspace-1");
    }
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined" && activeWorkspace) {
      window.localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(workspaces));
    }
  }, [workspaces, activeWorkspace]);

  useEffect(() => {
    if (!workspaces.some((workspace) => workspace.id === activeWorkspaceId)) {
      setActiveWorkspaceId(workspaces[0]?.id ?? "workspace-1");
    }
  }, [activeWorkspaceId, workspaces]);

  const loadDocuments = async () => {
    if (!activeWorkspace) return;
    try {
      const documents = await api.documents(projectId);
      setWorkspaces((current) =>
        current.map((workspace) =>
          workspace.id === activeWorkspace.id ? { ...workspace, documents } : workspace,
        ),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load documents.");
    }
  };

  useEffect(() => {
    setSelectedDocument(undefined);
    setElements([]);
    void loadDocuments();
  }, [projectId]);

  useEffect(() => {
    if (!selectedDocument || !["queued", "partitioning", "chunking", "summarizing", "vectorizing"].includes(selectedDocument.status)) {
      return;
    }

    const intervalId = window.setInterval(() => {
      setProgressByDocument((current) => {
        const startingPoint = current[selectedDocument.id] ?? getProgressForStatus(selectedDocument.status).progress;
        const nextValue = Math.min(100, startingPoint + 3 + Math.random() * 5);
        return { ...current, [selectedDocument.id]: nextValue };
      });
    }, 1100);

    return () => window.clearInterval(intervalId);
  }, [selectedDocument]);

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

  function getDocumentActionLabel(fileType: string): string {
    const normalized = fileType.toLowerCase();
    if (normalized === "pdf") return "Open PDF";
    if (normalized === "png" || normalized === "jpg" || normalized === "jpeg") return "Open Image";
    if (normalized === "txt" || normalized === "md") return "Open Text";
    if (normalized === "docx") return "Open Doc";
    if (normalized === "url") return "Open URL";
    return "Open File";
  }

  function openDocumentFile(documentId: string, filename: string, fileType: string) {
    const url = api.documentFileUrl(projectId, documentId);
    const label = getDocumentActionLabel(fileType);
    if (label === "Open Image" || label === "Open PDF" || label === "Open Text" || label === "Open Doc") {
      window.open(url, `_blank_${filename}`, "noopener,noreferrer");
      return;
    }
    window.open(url, `_blank_${filename}`, "noopener,noreferrer");
  }

  async function startConversation() {
    if (!activeWorkspace) return;
    try {
      const conversation = await api.createConversation(projectId);
      const nextSettings = await api.settings(projectId, conversation.id);
      setWorkspaces((current) =>
        current.map((workspace) =>
          workspace.id === activeWorkspace.id
            ? { ...workspace, conversationId: conversation.id, messages: [], settings: nextSettings }
            : workspace,
        ),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create a conversation.");
    }
  }

  async function submitQuestion() {
    if (!question.trim() || !conversationId) return;
    const content = question.trim();
    setQuestion("");
    setWorkspaces((current) =>
      current.map((workspace) =>
        workspace.id === activeWorkspaceId
          ? {
              ...workspace,
              messages: [
                ...workspace.messages,
                {
                  id: `local-${Date.now()}`,
                  sequence_number: workspace.messages.length,
                  role: "user",
                  content,
                  status: "complete",
                  failure_reason: null,
                  is_grounded: false,
                  created_at: "",
                  citations: [],
                },
              ],
            }
          : workspace,
      ),
    );
    setPhase("Retrieving sources");
    try {
      await ask(projectId, conversationId, content, (event, data) => {
        if (event === "phase") setPhase(data.phase === "generating" ? "Writing answer" : "Retrieving sources");
        if (event === "complete") {
          setWorkspaces((current) =>
            current.map((workspace) =>
              workspace.id === activeWorkspaceId
                ? {
                    ...workspace,
                    messages: [
                      ...workspace.messages,
                      {
                        id: String(data.message_id),
                        sequence_number: workspace.messages.length,
                        role: "assistant",
                        content: String(data.content),
                        status: "complete",
                        failure_reason: null,
                        is_grounded: Boolean(data.is_grounded),
                        created_at: "",
                        citations: (data.citations as Message["citations"]) ?? [],
                      },
                    ],
                  }
                : workspace,
            ),
          );
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
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      event.target.value = "";
    }
  }

  async function updateSettings(patch: Partial<Settings>) {
    if (!conversationId || !activeWorkspace) return;
    try {
      const nextSettings = await api.updateSettings(projectId, conversationId, patch);
      setWorkspaces((current) =>
        current.map((workspace) =>
          workspace.id === activeWorkspace.id ? { ...workspace, settings: nextSettings } : workspace,
        ),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save settings.");
    }
  }

  async function deleteDocument(documentId: string) {
    try {
      await api.deleteDocument(projectId, documentId);
      setWorkspaces((current) =>
        current.map((workspace) =>
          workspace.id === activeWorkspaceId
            ? { ...workspace, documents: workspace.documents.filter((document) => document.id !== documentId) }
            : workspace,
        ),
      );
      if (selectedDocument?.id === documentId) {
        setSelectedDocument(undefined);
        setElements([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete document.");
    }
  }

  function toggleDocumentType(type: string) {
    const types = settings.included_document_types.includes(type)
      ? settings.included_document_types.filter((item) => item !== type)
      : [...settings.included_document_types, type];
    if (types.length) {
      void updateSettings({ included_document_types: types });
    }
  }

  function addWorkspace() {
    const nextIndex = workspaces.length + 1;
    const nextWorkspace = buildWorkspace(`Workspace ${nextIndex}`, `workspace-${nextIndex}`);
    setWorkspaces((current) => [...current, nextWorkspace]);
    setActiveWorkspaceId(nextWorkspace.id);
  }

  function beginRenameWorkspace(workspace: Workspace) {
    setEditingWorkspaceId(workspace.id);
    setWorkspaceDraftName(workspace.name);
  }

  function finishRenameWorkspace() {
    if (!editingWorkspaceId) return;

    const trimmed = workspaceDraftName.trim();
    if (!trimmed) {
      setEditingWorkspaceId(null);
      setWorkspaceDraftName("");
      return;
    }

    setWorkspaces((current) =>
      current.map((workspace) =>
        workspace.id === editingWorkspaceId ? { ...workspace, name: trimmed } : workspace,
      ),
    );
    setEditingWorkspaceId(null);
    setWorkspaceDraftName("");
  }

  function deleteWorkspace(workspaceId: string) {
    if (workspaces.length <= 1) return;

    setWorkspaces((current) => {
      const remaining = current.filter((workspace) => workspace.id !== workspaceId);
      if (activeWorkspaceId === workspaceId) {
        setActiveWorkspaceId(remaining[0]?.id ?? "workspace-1");
      }
      return remaining;
    });

    if (editingWorkspaceId === workspaceId) {
      setEditingWorkspaceId(null);
      setWorkspaceDraftName("");
    }
  }

  const selectedProgress = selectedDocument
    ? progressByDocument[selectedDocument.id] ?? getProgressForStatus(selectedDocument.status).progress
    : 0;

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      if (!resizeStartRef.current) return;
      const { type, startX, startWidth } = resizeStartRef.current;
      const delta = event.clientX - startX;

      if (type === "rail") {
        setRailWidth(Math.min(320, Math.max(180, startWidth + delta)));
      }
      if (type === "documents") {
        setDocumentsWidth(Math.min(520, Math.max(260, startWidth + delta)));
      }
      if (type === "settings") {
        setSettingsPanelWidth(Math.min(420, Math.max(200, startWidth + delta)));
      }
    };

    const handleMouseUp = () => {
      resizeStartRef.current = null;
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  const beginResize = (type: "rail" | "documents" | "settings", event: React.MouseEvent<HTMLDivElement>) => {
    event.preventDefault();
    const startWidth = type === "rail" ? railWidth : type === "documents" ? documentsWidth : settingsPanelWidth;
    resizeStartRef.current = { type, startX: event.clientX, startWidth };
  };

  return (
    <main
      className={settingsOpen ? "workspace" : "workspace settings-collapsed"}
      style={{
        ["--rail-width" as string]: `${railWidth}px`,
        ["--documents-width" as string]: `${documentsWidth}px`,
        ["--settings-column-width" as string]: `${settingsOpen ? settingsPanelWidth : 72}px`,
      }}
    >
      <div className="orb orb-a" aria-hidden="true" />
      <div className="orb orb-b" aria-hidden="true" />
      <div className="orb orb-c" aria-hidden="true" />

      <aside className="rail glass" style={{ width: `${railWidth}px` }}>
        <div className="brand">
          <Sparkles size={18} /> AllSlate
        </div>
        <div className="workspace-switcher">
          <div className="workspace-switcher-header">
            <span className="eyebrow">Workspaces</span>
            <button type="button" className="plain-button small add-workspace-button" onClick={addWorkspace} aria-label="Add workspace">
              <Plus size={16} />
            </button>
          </div>
          {workspaces.map((workspace) => {
            const isEditing = editingWorkspaceId === workspace.id;
            const isActive = workspace.id === activeWorkspaceId;
            const showWorkspaceActions = expandedWorkspaceId === workspace.id && !isEditing;

            return (
              <div key={workspace.id} className={isActive ? `workspace-item active ${showWorkspaceActions ? "expanded" : ""}` : `workspace-item ${showWorkspaceActions ? "expanded" : ""}`}>
                {isEditing ? (
                  <div className="workspace-name-editor">
                    <input
                      value={workspaceDraftName}
                      onChange={(event) => setWorkspaceDraftName(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") finishRenameWorkspace();
                        if (event.key === "Escape") {
                          setEditingWorkspaceId(null);
                          setWorkspaceDraftName("");
                        }
                      }}
                      autoFocus
                    />
                    <div className="workspace-inline-actions">
                      <button type="button" className="mini-button success" onClick={finishRenameWorkspace} aria-label="Save workspace name">
                        <Check size={12} />
                      </button>
                      <button
                        type="button"
                        className="mini-button"
                        onClick={() => {
                          setEditingWorkspaceId(null);
                          setWorkspaceDraftName("");
                        }}
                        aria-label="Cancel workspace rename"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <button
                      type="button"
                      className={isActive ? "project-switch active" : "project-switch"}
                      onClick={() => {
                        setActiveWorkspaceId(workspace.id);
                        setExpandedWorkspaceId((current) => (current === workspace.id ? null : workspace.id));
                      }}
                    >
                      <span className="project-mark">{workspace.name.slice(0, 1).toUpperCase()}</span>
                      <span>{workspace.name}</span>
                      <ChevronRight size={15} />
                    </button>
                    <div className={`workspace-actions ${showWorkspaceActions ? "visible" : ""}`}>
                      <button type="button" className="mini-button" onClick={() => beginRenameWorkspace(workspace)} aria-label={`Rename ${workspace.name}`}>
                        <Pencil size={12} />
                      </button>
                      <button type="button" className="mini-button danger" onClick={() => deleteWorkspace(workspace.id)} aria-label={`Delete ${workspace.name}`}>
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
        <div className="rail-bottom">
          <ThemeToggle />
          <button type="button" onClick={() => setSettingsOpen((value) => !value)}>
            <Settings2 size={18} /> Preferences
          </button>
          <div className="avatar">N</div>
        </div>
      </aside>

      <div className="column-divider rail-divider" onMouseDown={(event) => beginResize("rail", event)} aria-label="Resize workspace column" role="separator" tabIndex={0} />

      <section className="documents glass" style={{ width: `${documentsWidth}px` }}>
        <header>
          <div>
            <p className="eyebrow">Project library</p>
            <h1>{activeWorkspace?.name ?? "Workspace"}</h1>
          </div>
          <label className="icon-button" title="Upload document">
            <Upload size={18} />
            <input type="file" onChange={upload} />
          </label>
        </header>
        <div className="document-list">
          {(activeWorkspace?.documents ?? []).map((document) => {
            const progress = progressByDocument[document.id] ?? getProgressForStatus(document.status).progress;
            const eta = Math.max(0, Math.ceil((100 - progress) / 12));
            return (
              <div key={document.id} className={selectedDocument?.id === document.id ? "document-card selected" : "document-card"}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <button type="button" className="document-row" onClick={() => void openDocument(document.id)}>
                    <FileText size={18} />
                    <span>
                      <strong>{document.filename}</strong>
                      <small>{document.file_type.toUpperCase()} · {document.status.replace("_", " ")}</small>
                    </span>
                  </button>
                  <div className="document-actions">
                    <button type="button" className="pdf-button" onClick={(event) => {
                      event.stopPropagation();
                      openDocumentFile(document.id, document.filename, document.file_type);
                    }}>
                      {getDocumentActionLabel(document.file_type)}
                    </button>
                    <button type="button" className="delete-document" onClick={(event) => {
                      event.stopPropagation();
                      void deleteDocument(document.id);
                    }} aria-label={`Delete ${document.filename}`}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
                {document.status !== "stored" && document.status !== "failed" && document.status !== "stored_partial" && (
                  <div className="document-progress" aria-live="polite">
                    <div className="document-progress-bar" style={{ width: `${progress}%` }} />
                    <div className="document-progress-meta">
                      <span>{progress}%</span>
                      <span>{eta}s left</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        {selectedDocument && (
          <section className="inspection">
            <div className="inspection-heading">
              <div>
                <p className="eyebrow">Inspection</p>
                <h2>{selectedDocument.filename}</h2>
              </div>
              <button type="button" className="plain-button" onClick={() => setSelectedDocument(undefined)}>
                <X size={16} />
              </button>
            </div>
            {selectedDocument.status !== "stored" && selectedDocument.status !== "failed" && selectedDocument.status !== "stored_partial" && (
              <div className="processing-panel">
                <div className="processing-copy">
                  <span>Partitioning</span>
                  <strong>{selectedProgress}%</strong>
                </div>
                <div className="status-track">
                  <div className="status-fill" style={{ width: `${selectedProgress}%` }} />
                </div>
                <small>
                  {Math.max(0, Math.ceil((100 - selectedProgress) / 12))}s remaining
                </small>
              </div>
            )}
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

      <div className="column-divider documents-divider" onMouseDown={(event) => beginResize("documents", event)} aria-label="Resize library column" role="separator" tabIndex={0} />

      <section className="chat glass">
        <header>
          <div>
            <p className="eyebrow">Workspace</p>
            <h1>Ask your library</h1>
          </div>
          <button type="button" onClick={() => void startConversation()} className="new-chat">
            <MessageSquarePlus size={17} /> New chat
          </button>
        </header>
        {!conversationId ? (
          <TiltCard className="empty-chat">
            <div className="spark">
              <Bot size={26} />
            </div>
            <h2>Start with a question</h2>
            <p>AllSlate finds the relevant material in your workspace and keeps every answer tied to its source.</p>
            <button type="button" onClick={() => void startConversation()} className="primary">
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
                        <button type="button" onClick={() => void openDocument(citation.document_id)} key={`${citation.document_id}-${index}`}>
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
            <form
              onSubmit={(event) => {
                event.preventDefault();
                void submitQuestion();
              }}
              className="composer"
            >
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event: KeyboardEvent<HTMLTextAreaElement>) => {
                  if (event.key === "Enter" && !event.metaKey && !event.ctrlKey && !event.altKey) {
                    event.preventDefault();
                    void submitQuestion();
                  }
                }}
                placeholder="Ask a question about your documents..."
                rows={2}
              />
              <button type="submit" className="send" aria-label="Send question" disabled={!question.trim() || Boolean(phase)}>
                <Send size={18} />
              </button>
            </form>
          </>
        )}
      </section>

      <div className="column-divider settings-divider" onMouseDown={(event) => beginResize("settings", event)} aria-label="Resize settings column" role="separator" tabIndex={0} />

      <aside
        className={settingsOpen ? "settings-panel glass open" : "settings-panel glass"}
        style={{ width: `${settingsOpen ? settingsPanelWidth : 72}px` }}
      >
        <button type="button" className="settings-toggle" title="Toggle settings" onClick={() => setSettingsOpen((value) => !value)}>
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
                onChange={(event) => void updateSettings({ web_search_enabled: event.target.checked })}
              />
            </label>
            <fieldset disabled={!conversationId}>
              <legend>Response style</legend>
              <div className="segmented">
                {RESPONSE_STYLES.map((level) => (
                  <button
                    type="button"
                    onClick={() => void updateSettings({ creativity_level: level })}
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
                onChange={(event) => void updateSettings({ retrieval_top_k: Number(event.target.value) })}
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
          <button type="button" onClick={() => setError("")}>
            <X size={15} />
          </button>
        </div>
      )}
    </main>
  );
}
