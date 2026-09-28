import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

// 1x1 Transparent PNG buffer (68 bytes) to serve for out-of-bounds / unsupported zoom tiles
const TRANSPARENT_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSU5EUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "base64"
);

import { BACKEND_URL } from "@/lib/api/client";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ z: string; x: string; y: string }> }
) {
  const { z, x, y } = await context.params;
  const cleanY = y.replace(/\.png$/, "");

  // 1. Proxy request directly to FastAPI backend dynamic tile endpoint (RGBA)
  try {
    const backendTileUrl = `${BACKEND_URL}/api/v1/tiles/bhopal/${z}/${x}/${cleanY}.png`;
    const res = await fetch(backendTileUrl);
    if (res.ok) {
      const buffer = await res.arrayBuffer();
      return new NextResponse(buffer, {
        status: 200,
        headers: {
          "Content-Type": "image/png",
          "Cache-Control": "public, max-age=86400",
        },
      });
    }
  } catch (proxyErr) {
    // Backend fallback failed
  }

  // 3. Fallback to transparent PNG if backend is unreachable or out of bounds
  return new NextResponse(TRANSPARENT_PNG, {
    status: 200,
    headers: {
      "Content-Type": "image/png",
      "Cache-Control": "public, max-age=3600",
    },
  });
}
