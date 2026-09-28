import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET(request: NextRequest) {
  const { search } = new URL(request.url);
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/exports/formats${search}`, { cache: "no-store" });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error: any) {
    return NextResponse.json({ error: "Failed to connect to export service" }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const res = await fetch(`${BACKEND_URL}/api/v1/exports`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const fileBuffer = await res.arrayBuffer();
    const contentType = res.headers.get("content-type") ?? "application/octet-stream";
    const disposition = res.headers.get("content-disposition") ?? "attachment; filename=DrishtiGIS_Export.geojson";

    return new NextResponse(fileBuffer, {
      status: res.status,
      headers: {
        "Content-Type": contentType,
        "Content-Disposition": disposition,
      },
    });
  } catch (error: any) {
    return NextResponse.json({ error: "Failed to generate GIS export" }, { status: 500 });
  }
}
