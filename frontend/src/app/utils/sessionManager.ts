// Session management utilities for persistent authentication

export const SESSION_DURATION = 24 * 60 * 60 * 1000; // 24 hours
export const WARNING_THRESHOLD = 5 * 60 * 1000; // Show warning 5 minutes before expiry

export interface SessionData {
  token: string;
  expiry: number;
  user: {
    operatorId: string;
    role: string;
    loginTime: string;
  };
}

/**
 * Check if the current session is valid
 */
export function isSessionValid(): boolean {
  const sessionToken = localStorage.getItem("sessionToken");
  const sessionExpiry = localStorage.getItem("sessionExpiry");

  if (!sessionToken || !sessionExpiry) {
    return false;
  }

  const expiryTime = parseInt(sessionExpiry);
  const now = Date.now();

  return now < expiryTime;
}

/**
 * Get remaining session time in milliseconds
 */
export function getSessionTimeRemaining(): number {
  const sessionExpiry = localStorage.getItem("sessionExpiry");
  if (!sessionExpiry) return 0;

  const expiryTime = parseInt(sessionExpiry);
  const now = Date.now();

  return Math.max(0, expiryTime - now);
}

/**
 * Check if session is about to expire (within warning threshold)
 */
export function isSessionExpiringSoon(): boolean {
  const remaining = getSessionTimeRemaining();
  return remaining > 0 && remaining <= WARNING_THRESHOLD;
}

/**
 * Extend the current session by the full duration
 */
export function extendSession(): void {
  const newExpiry = Date.now() + SESSION_DURATION;
  localStorage.setItem("sessionExpiry", newExpiry.toString());
}

/**
 * Clear all session data (logout)
 */
export function clearSession(): void {
  localStorage.removeItem("sessionToken");
  localStorage.removeItem("sessionExpiry");
  sessionStorage.removeItem("currentUser");
}

/**
 * Get current user from session storage
 */
export function getCurrentUser(): { operatorId: string; role: string; loginTime: string } | null {
  const userStr = sessionStorage.getItem("currentUser");
  if (!userStr) return null;

  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

/**
 * Format time remaining in human-readable format
 */
export function formatTimeRemaining(ms: number): string {
  const minutes = Math.floor(ms / 60000);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  }
  return `${minutes}m`;
}
