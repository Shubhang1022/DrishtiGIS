import type { Metadata } from "next";
import { Inter, Playfair_Display, Geist } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});


// ---- Display / editorial serif (headlines, hero text)
const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
  variable: "--font-display-loaded",
  display: "swap",
});

// ---- UI / interface sans-serif
const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-ui-loaded",
  display: "swap",
});

export const metadata: Metadata = {
  title: "DrishtiGIS — A Clearer View of a Brighter Tomorrow",
  description:
    "AI-powered urban geospatial intelligence platform for parcel mapping, " +
    "cadastral feature extraction, and discrepancy detection.",
};

import { AuthProvider } from "@/lib/auth/Context";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={cn(playfair.variable, inter.variable, "font-sans", geist.variable)}
      suppressHydrationWarning
    >
      <body className="antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
