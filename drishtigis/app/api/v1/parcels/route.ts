import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const city = searchParams.get("city");

  const candidatePaths = [
    path.resolve(process.cwd(), "lib", "demo-data", "bhopal-parcels.geojson"),
    path.resolve(process.cwd(), "..", "drishtigis", "lib", "demo-data", "bhopal-parcels.geojson"),
  ];

  if (city && city.toLowerCase() !== "bhopal") {
    return NextResponse.json({
      type: "FeatureCollection",
      total: 0,
      features: [],
      _source: "DEMO_DATA_PROTOTYPE_ONLY",
      _coverage_note: `No parcel data available for ${city}. DrishtiGIS currently has prototype data for Bhopal only.`,
    });
  }

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
        console.error("Error reading parcels file:", err);
      }
    }
  }

  return new NextResponse("Parcels GeoJSON file not found", { status: 404 });
}
