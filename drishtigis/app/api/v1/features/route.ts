import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET(request: NextRequest) {
  const candidatePaths = [
    path.resolve(process.cwd(), "..", "data", "ai_output", "bhopal-building-parcel-associations.geojson"),
    path.resolve(process.cwd(), "data", "ai_output", "bhopal-building-parcel-associations.geojson"),
    path.resolve(process.cwd(), "lib", "demo-data", "bhopal-ai-features.geojson"),
    path.resolve(process.cwd(), "..", "drishtigis", "lib", "demo-data", "bhopal-ai-features.geojson"),
  ];

  for (const filePath of candidatePaths) {
    if (fs.existsSync(/*turbopackIgnore: true*/ filePath)) {
      try {
        const fileBuffer = await fs.promises.readFile(/*turbopackIgnore: true*/ filePath);
        return new NextResponse(fileBuffer, {
          status: 200,
          headers: {
            "Content-Type": "application/geo+json",
            "X-Data-Status": "demo-placeholder",
            "Cache-Control": "public, max-age=1800, immutable",
          },
        });
      } catch (err) {
        console.error("Error reading AI features file:", err);
      }
    }
  }

  return new NextResponse("AI features GeoJSON file not found", { status: 404 });
}
