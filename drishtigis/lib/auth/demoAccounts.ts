/**
 * DrishtiGIS — SIH Demo Account Registry & Verification
 * =======================================================
 * Preserves the 4 SIH26012 evaluation accounts for reviewer testing while allowing
 * real users to authenticate through Supabase Auth for private, isolated HOME locations.
 */

export const DEFAULT_DEMO_EMAILS = [
  "demo-public@drishtigis.in",
  "demo-surveyor@drishtigis.in",
  "demo-reviewer@drishtigis.in",
  "demo-admin@drishtigis.in",
];

export interface DemoAccountInfo {
  email: string;
  label: string;
  description: string;
  badgeColor: string;
  defaultPass: string;
}

export const SIH_DEMO_ACCOUNTS: DemoAccountInfo[] = [
  {
    email: "demo-public@drishtigis.in",
    label: "Public Citizen",
    description: "Read-only public data",
    badgeColor: "#2C2C2C",
    defaultPass: "Public123!",
  },
  {
    email: "demo-surveyor@drishtigis.in",
    label: "Field Surveyor",
    description: "Geometry editing & ground survey",
    badgeColor: "#2D5016",
    defaultPass: "Surveyor123!",
  },
  {
    email: "demo-reviewer@drishtigis.in",
    label: "Reviewer / Approver",
    description: "Approve/reject field edits",
    badgeColor: "#854d0e",
    defaultPass: "Reviewer123!",
  },
  {
    email: "demo-admin@drishtigis.in",
    label: "System Admin",
    description: "Full platform governance",
    badgeColor: "#881337",
    defaultPass: "Admin123!",
  },
];

/**
 * Returns the set of all emails designated as demo evaluation accounts.
 * Reads from NEXT_PUBLIC_DEMO_AUTH_EMAILS if set, otherwise uses DEFAULT_DEMO_EMAILS.
 */
export function getDemoEmails(): Set<string> {
  const envEmails = process.env.NEXT_PUBLIC_DEMO_AUTH_EMAILS;
  if (envEmails && envEmails.trim()) {
    const list = envEmails
      .split(",")
      .map((e) => e.trim().toLowerCase())
      .filter(Boolean);
    if (list.length > 0) {
      return new Set(list);
    }
  }
  return new Set(DEFAULT_DEMO_EMAILS.map((e) => e.toLowerCase()));
}

/**
 * Checks whether the given email belongs to an SIH demo evaluation account.
 */
export function isDemoEmail(email: string): boolean {
  if (!email) return false;
  const cleanEmail = email.trim().toLowerCase();
  const demoSet = getDemoEmails();
  return demoSet.has(cleanEmail) || cleanEmail.startsWith("demo-");
}
