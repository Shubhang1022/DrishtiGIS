import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { BACKEND_URL } from "@/lib/api/client";

const ALLOWED_LAYERS = new Set(["buildings", "roads", "waterways", "landuse"]);

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ layer: string }> }
) {
  const { layer } = await context.params;

  if (!ALLOWED_LAYERS.has(layer)) {
    return new NextResponse(`Layer '${layer}' not allowed`, { status: 404 });
  }

  const candidatePaths = [
    path.resolve(process.cwd(), "..", "data", "osm", "bhopal-extract", `bhopal-${layer}.geojson`),
    path.resolve(process.cwd(), "data", "osm", "bhopal-extract", `bhopal-${layer}.geojson`),
  ];

  for (const filePath of candidatePaths) {
    if (fs.existsSync(/*turbopackIgnore: true*/ filePath)) {
      try {
        const fileBuffer = await fs.promises.readFile(/*turbopackIgnore: true*/ filePath);
        return new NextResponse(fileBuffer, {
          status: 200,
          headers: {
            "Content-Type": "application/geo+json",
            "X-OSM-Attribution": "(c) OpenStreetMap contributors, ODbL",
            "Cache-Control": "public, max-age=1800, immutable",
          },
        });
      } catch (err) {
        console.error(`Error reading OSM layer file for ${layer}:`, err);
      }
    }
  }

  // Fallback: proxy to backend for hosted/serverless environments where data files are on EC2
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/osm/bhopal/${layer}`);
    if (res.ok) {
      const data = await res.arrayBuffer();
      return new NextResponse(data, {
        status: 200,
        headers: {
          "Content-Type": "application/geo+json",
          "X-OSM-Attribution": "(c) OpenStreetMap contributors, ODbL",
          "Cache-Control": "public, max-age=1800",
        },
      });
    }
  } catch (err) {
    console.error(`Error proxying OSM layer ${layer} to backend:`, err);
  }

  return new NextResponse(`OSM layer file for '${layer}' not found`, { status: 404 });
}
