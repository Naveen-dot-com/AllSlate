export type DocumentItem = { id: string; filename: string; file_type: string; status: string; uploaded_at: string };
export type DocumentDetail = DocumentItem & { failure_category: string | null; has_low_confidence_content: boolean; element_count: number; element_counts_by_type: Record<string, number> };
export type ElementItem = { id: string; element_type: string; page_number: number | null; confidence: "confident" | "partial" | "uncertain"; confidence_reason: string | null };
export type Citation = { document_id: string; page_number: number | null; asset_reference_url: string | null };
export type Message = { id: string; sequence_number: number; role: "user" | "assistant"; content: string; status: "complete" | "pending" | "failed"; failure_reason: string | null; is_grounded: boolean; created_at: string; citations: Citation[] };
export type Settings = { web_search_enabled: boolean; creativity_level: "focused" | "balanced" | "creative"; retrieval_top_k: number; included_document_types: string[]; updated_at: string };

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, { ...options, headers: { "Content-Type": "application/json", ...options?.headers } });
  if (!response.ok) throw new Error((await response.text()) || "The request could not be completed.");
  return response.json() as Promise<T>;
}

export const api = {
  documents: (projectId: string) => request<DocumentItem[]>(`/projects/${projectId}/documents`),
  document: (projectId: string, documentId: string) => request<DocumentDetail>(`/projects/${projectId}/documents/${documentId}`),
  elements: (projectId: string, documentId: string) => request<ElementItem[]>(`/projects/${projectId}/documents/${documentId}/elements`),
  upload: (projectId: string, file: File) => { const body = new FormData(); body.append("file", file); return fetch(`/api/v1/projects/${projectId}/documents`, { method: "POST", body }).then(async response => { if (!response.ok) throw new Error(await response.text()); return response.json() as Promise<DocumentItem>; }); },
  createConversation: (projectId: string) => request<{ id: string }>(`/projects/${projectId}/conversations`, { method: "POST", body: JSON.stringify({}) }),
  messages: (projectId: string, conversationId: string) => request<Message[]>(`/projects/${projectId}/conversations/${conversationId}/messages`),
  settings: (projectId: string, conversationId: string) => request<Settings>(`/projects/${projectId}/conversations/${conversationId}/settings`),
  updateSettings: (projectId: string, conversationId: string, patch: Partial<Settings>) => request<Settings>(`/projects/${projectId}/conversations/${conversationId}/settings`, { method: "PATCH", body: JSON.stringify(patch) }),
};

export async function ask(projectId: string, conversationId: string, question: string, onEvent: (event: string, data: Record<string, unknown>) => void) {
  const response = await fetch(`/api/v1/projects/${projectId}/conversations/${conversationId}/ask`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
  if (!response.ok || !response.body) throw new Error((await response.text()) || "Unable to start the answer.");
  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = "";
  for (;;) { const { done, value } = await reader.read(); if (done) break; buffer += decoder.decode(value, { stream: true }); const frames = buffer.split("\n\n"); buffer = frames.pop() ?? ""; for (const frame of frames) { const event = frame.match(/^event: (.+)$/m)?.[1] ?? "message"; const raw = frame.match(/^data: (.+)$/m)?.[1]; if (raw) onEvent(event, JSON.parse(raw)); } }
}