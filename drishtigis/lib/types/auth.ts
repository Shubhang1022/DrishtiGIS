export type UserRole = "PUBLIC" | "SURVEYOR" | "REVIEWER" | "ADMIN" | "DATA_MANAGER";

export interface User {
  user_id: string;
  email: string;
  name: string;
  role: UserRole;
  organization?: string;
  country: string;
  state?: string;
  city?: string;
  region_id?: string;
  allowed_datasets: string[];
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface SecurityAuditLogItem {
  audit_id: string;
  user_id: string;
  user_email: string;
  role: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  timestamp: string;
  region_id?: string;
  dataset_id?: string;
  details?: Record<string, any>;
}
