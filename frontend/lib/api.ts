export type DocumentItem = { id: string; filename: string; file_type: string; status: string; uploaded_at: string; file_data_url?: string };
export type DocumentDetail = DocumentItem & { failure_category: string | null; has_low_confidence_content: boolean; element_count: number; element_counts_by_type: Record<string, number> };
export type ElementItem = { id: string; element_type: string; page_number: number | null; confidence: "confident" | "partial" | "uncertain"; confidence_reason: string | null };
export type Citation = { document_id: string; page_number: number | null; asset_reference_url: string | null };
export type Message = { id: string; sequence_number: number; role: "user" | "assistant"; content: string; status: "complete" | "pending" | "failed"; failure_reason: string | null; is_grounded: boolean; created_at: string; citations: Citation[] };
export type Settings = { web_search_enabled: boolean; creativity_level: "focused" | "precise" | "balanced" | "creative"; retrieval_top_k: number; included_document_types: string[]; updated_at: string };

const API_BASE = process.env.NEXT_PUBLIC_ALLSLATE_API_URL ?? "";
const DEMO_STORAGE_KEY = "allslate-demo-state-v1";
const DEFAULT_SETTINGS: Settings = {
  web_search_enabled: false,
  creativity_level: "balanced",
  retrieval_top_k: 6,
  included_document_types: ["text", "table", "image"],
  updated_at: new Date().toISOString(),
};

type DemoState = {
  [projectId: string]: {
    documents: DocumentItem[];
    conversations: Record<string, { id: string; settings: Settings; messages: Message[] }>;
  };
};

function projectStore(projectId: string): { documents: DocumentItem[]; conversations: Record<string, { id: string; settings: Settings; messages: Message[] }> } {
  if (typeof window === "undefined") {
    return { documents: [], conversations: {} };
  }

  try {
    const raw = window.localStorage.getItem(DEMO_STORAGE_KEY);
    const parsed = raw ? (JSON.parse(raw) as DemoState) : {};
    const existing = parsed[projectId] ?? { documents: [], conversations: {} };
    return {
      documents: existing.documents ?? [],
      conversations: existing.conversations ?? {},
    };
  } catch {
    return { documents: [], conversations: {} };
  }
}

function writeProjectStore(projectId: string, next: { documents: DocumentItem[]; conversations: Record<string, { id: string; settings: Settings; messages: Message[] }> }) {
  if (typeof window === "undefined") return;

  try {
    const raw = window.localStorage.getItem(DEMO_STORAGE_KEY);
    const parsed = raw ? (JSON.parse(raw) as DemoState) : {};
    parsed[projectId] = next;
    window.localStorage.setItem(DEMO_STORAGE_KEY, JSON.stringify(parsed));
  } catch {
    // Ignore local storage failures.
  }
}

function normalizeFileType(file: File): string {
  const extension = file.name.split(".").pop()?.toLowerCase();
  if (extension) return extension;
  return file.type.split("/")[1] ?? "file";
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(new Error("Could not read the file."));
    reader.readAsDataURL(file);
  });
}

function localApiUrl(path: string) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (normalized.startsWith("/api")) {
    return normalized;
  }
  return `/api${normalized}`;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const backendConfigured = Boolean(API_BASE);
  if (!backendConfigured && typeof window !== "undefined") {
    const urlPath = path.startsWith("/v1") ? path.slice(3) : path;
    const method = (options?.method ?? "GET").toUpperCase();
    const projectId = urlPath.match(/\/projects\/([^/]+)/)?.[1];
    const documentId = urlPath.match(/\/documents\/([^/]+)(?:\/|$)/)?.[1];
    const conversationId = urlPath.match(/\/conversations\/([^/]+)(?:\/|$)/)?.[1];

    if (method === "GET" && urlPath.includes("/documents") && !documentId && projectId) {
      return Promise.resolve(projectStore(projectId).documents as T);
    }

    if (method === "GET" && documentId && urlPath.includes(`/documents/${documentId}`) && projectId) {
      const doc = projectStore(projectId).documents.find((item) => item.id === documentId);
      if (!doc) throw new Error("Document not found.");
      return Promise.resolve({
        ...doc,
        failure_category: null,
        has_low_confidence_content: false,
        element_count: 1,
        element_counts_by_type: { [doc.file_type]: 1 },
      } as T);
    }

    if (method === "GET" && documentId && urlPath.includes(`/documents/${documentId}/elements`) && projectId) {
      const doc = projectStore(projectId).documents.find((item) => item.id === documentId);
      if (!doc) throw new Error("Document not found.");
      return Promise.resolve([
        {
          id: `${doc.id}-element-1`,
          element_type: doc.file_type === "image" ? "image" : "text",
          page_number: 1,
          confidence: "confident",
          confidence_reason: "Local demo index generated from the uploaded file.",
        },
      ] as T);
    }

    if (method === "DELETE" && documentId && projectId) {
      const state = projectStore(projectId);
      const nextDocs = state.documents.filter((item) => item.id !== documentId);
      writeProjectStore(projectId, { ...state, documents: nextDocs });
      return Promise.resolve({ deleted: true, document_id: documentId } as T);
    }

    if (method === "POST" && urlPath.includes("/conversations") && !conversationId && projectId) {
      const state = projectStore(projectId);
      const id = `conversation-${Date.now()}`;
      state.conversations[id] = { id, settings: { ...DEFAULT_SETTINGS }, messages: [] };
      writeProjectStore(projectId, state);
      return Promise.resolve({ id } as T);
    }

    if (method === "GET" && conversationId && urlPath.includes(`/conversations/${conversationId}/settings`) && projectId) {
      const state = projectStore(projectId);
      const settings = state.conversations[conversationId]?.settings ?? { ...DEFAULT_SETTINGS };
      return Promise.resolve(settings as T);
    }

    if (method === "PATCH" && conversationId && urlPath.includes(`/conversations/${conversationId}/settings`) && projectId) {
      const state = projectStore(projectId);
      const existing = state.conversations[conversationId] ?? { id: conversationId, settings: { ...DEFAULT_SETTINGS }, messages: [] };
      const patched = { ...existing.settings, ...JSON.parse((options?.body as string) ?? "{}"), updated_at: new Date().toISOString() } as Settings;
      existing.settings = patched;
      state.conversations[conversationId] = existing;
      writeProjectStore(projectId, state);
      return Promise.resolve(patched as T);
    }

    if (method === "GET" && conversationId && urlPath.includes(`/conversations/${conversationId}/messages`) && projectId) {
      const state = projectStore(projectId);
      return Promise.resolve((state.conversations[conversationId]?.messages ?? []) as T);
    }
  }

  const response = await fetch(localApiUrl(`/v1${path}`), { ...options, headers: { "Content-Type": "application/json", ...options?.headers } });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "The request could not be completed.");
  }
  return response.json() as Promise<T>;
}

export const api = {
  documents: (projectId: string) => request<DocumentItem[]>(`/projects/${projectId}/documents`),
  document: (projectId: string, documentId: string) => request<DocumentDetail>(`/projects/${projectId}/documents/${documentId}`),
  elements: (projectId: string, documentId: string) => request<ElementItem[]>(`/projects/${projectId}/documents/${documentId}/elements`),
  documentFileUrl: (projectId: string, documentId: string) => {
    if (typeof window === "undefined") return "";
    if (API_BASE) {
      return localApiUrl(`/v1/projects/${projectId}/documents/${documentId}/file`);
    }

    const state = projectStore(projectId);
    const document = state.documents.find((item) => item.id === documentId);
    if (document?.file_data_url) return document.file_data_url;

    if (document?.file_type === "pdf") {
      return `data:application/pdf;base64,${btoa(`%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF`)}`;
    }

    if (document?.file_type === "txt" || document?.file_type === "md") {
      return `data:text/plain;charset=utf-8,${encodeURIComponent(`Demo document: ${document?.filename ?? documentId}`)}`;
    }

    return `data:text/plain;base64,${btoa(`Demo document: ${document?.filename ?? documentId}`)}`;
  },
  upload: async (projectId: string, file: File) => {
    if (!API_BASE && typeof window !== "undefined") {
      const documentId = crypto.randomUUID();
      const file_data_url = await fileToDataUrl(file);
      const state = projectStore(projectId);
      const nextDocument: DocumentItem = {
        id: documentId,
        filename: file.name,
        file_type: normalizeFileType(file),
        status: "stored",
        uploaded_at: new Date().toISOString(),
        file_data_url,
      };
      writeProjectStore(projectId, { ...state, documents: [nextDocument, ...state.documents] });
      return nextDocument;
    }

    const body = new FormData();
    body.append("file", file);
    const response = await fetch(localApiUrl(`/v1/projects/${projectId}/documents`), { method: "POST", body });
    if (!response.ok) throw new Error(await response.text());
    return response.json() as Promise<DocumentItem>;
  },
  deleteDocument: (projectId: string, documentId: string) => request<{ deleted: boolean; document_id: string }>(`/projects/${projectId}/documents/${documentId}`, { method: "DELETE" }),
  createConversation: (projectId: string) => request<{ id: string }>(`/projects/${projectId}/conversations`, { method: "POST", body: JSON.stringify({}) }),
  messages: (projectId: string, conversationId: string) => request<Message[]>(`/projects/${projectId}/conversations/${conversationId}/messages`),
  settings: (projectId: string, conversationId: string) => request<Settings>(`/projects/${projectId}/conversations/${conversationId}/settings`),
  updateSettings: (projectId: string, conversationId: string, patch: Partial<Settings>) => request<Settings>(`/projects/${projectId}/conversations/${conversationId}/settings`, { method: "PATCH", body: JSON.stringify(patch) }),
};

export async function ask(projectId: string, conversationId: string, question: string, onEvent: (event: string, data: Record<string, unknown>) => void) {
  if (!API_BASE && typeof window !== "undefined") {
    onEvent("phase", { phase: "retrieving" });
    await new Promise((resolve) => window.setTimeout(resolve, 180));
    onEvent("phase", { phase: "generating" });

    const state = projectStore(projectId);
    const docs = state.documents;
    const grounded = docs.length ? docs.slice(0, Math.min(3, docs.length)) : [];
    const content = grounded.length
      ? `I found ${grounded.length} uploaded document${grounded.length === 1 ? "" : "s"} relevant to “${question}” in this local workspace. This demo mode is ready, but a real backend will supply the full answer grounding and citations.`
      : `This workspace is running in local demo mode. Upload a document and ask a question to test the flow. A real backend can power deeper retrieval and grounded answers.`;

    const messageId = `assistant-${Date.now()}`;
    const citations = grounded.map((document) => ({ document_id: document.id, page_number: 1, asset_reference_url: document.file_data_url ?? null }));
    const conversation = state.conversations[conversationId] ?? { id: conversationId, settings: { ...DEFAULT_SETTINGS }, messages: [] };
    conversation.messages.push({
      id: messageId,
      sequence_number: conversation.messages.length,
      role: "assistant",
      content,
      status: "complete",
      failure_reason: null,
      is_grounded: grounded.length > 0,
      created_at: new Date().toISOString(),
      citations,
    });
    state.conversations[conversationId] = conversation;
    writeProjectStore(projectId, state);
    onEvent("complete", { message_id: messageId, content, is_grounded: grounded.length > 0, citations });
    return;
  }

  const response = await fetch(localApiUrl(`/v1/projects/${projectId}/conversations/${conversationId}/ask`), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
  if (!response.ok || !response.body) throw new Error((await response.text()) || "Unable to start the answer.");
  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = "";
  for (;;) { const { done, value } = await reader.read(); if (done) break; buffer += decoder.decode(value, { stream: true }); const frames = buffer.split("\n\n"); buffer = frames.pop() ?? ""; for (const frame of frames) { const event = frame.match(/^event: (.+)$/m)?.[1] ?? "message"; const raw = frame.match(/^data: (.+)$/m)?.[1]; if (raw) onEvent(event, JSON.parse(raw)); } }
}