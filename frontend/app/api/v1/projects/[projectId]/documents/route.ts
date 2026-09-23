import { NextRequest, NextResponse } from "next/server";

const externalBase = process.env.ALLSLATE_API_URL ?? process.env.NEXT_PUBLIC_ALLSLATE_API_URL;

export async function POST(req: NextRequest, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  const formData = await req.formData();
  const file = formData.get("file");

  if (!(file instanceof File)) {
    return NextResponse.json({ error: "No file uploaded." }, { status: 400 });
  }

  if (!externalBase) {
    return NextResponse.json({
      id: crypto.randomUUID(),
      filename: file.name,
      file_type: file.name.split(".").pop()?.toLowerCase() || "unknown",
      status: "stored",
      uploaded_at: new Date().toISOString(),
    }, { status: 200 });
  }

  const payload = await file.arrayBuffer();
  const upstream = `${externalBase}/api/v1/projects/${projectId}/documents`;
  try {
    const response = await fetch(upstream, {
      method: "POST",
      headers: { "x-forwarded-project-id": projectId },
      body: (() => {
        const form = new FormData();
        form.append("file", new Blob([payload], { type: file.type || "application/octet-stream" }), file.name);
        return form;
      })(),
    });
    const text = await response.text();
    if (!response.ok) {
      return NextResponse.json({ error: text || "Upload failed." }, { status: response.status });
    }
    return NextResponse.json(JSON.parse(text || "{}"), { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Upload failed." }, { status: 500 });
  }
}

export async function GET(req: NextRequest, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;

  if (!externalBase) {
    return NextResponse.json([
      {
        id: `demo-${projectId}-document-1`,
        filename: "demo-upload.txt",
        file_type: "txt",
        status: "stored",
        uploaded_at: new Date().toISOString(),
      },
    ]);
  }

  const upstream = `${externalBase}/api/v1/projects/${projectId}/documents`;
  try {
    const response = await fetch(upstream);
    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: { "Content-Type": response.headers.get("content-type") ?? "application/json" },
    });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Unable to load documents." }, { status: 500 });
  }
}
