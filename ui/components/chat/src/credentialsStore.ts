// Credential persistence in localStorage, scoped per provider.
//
// Storage shape: { [providerId]: { [fieldId]: value } }
// Values are written and read verbatim; the component is the only caller.
// A user opening browser devtools can see their own key — that's the stated
// privacy bar ("key in memory for the duration of a turn, never server-side").

import type { CredentialField } from "./types";

const STORAGE_KEY = "beril.chat.credentials";

type CredentialStore = Record<string, Record<string, string>>;

function read(): CredentialStore {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return {};
    return parsed as CredentialStore;
  } catch {
    // Corrupt entry — drop it and start fresh.
    return {};
  }
}

function write(store: CredentialStore): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
}

export function getCredentialsFor(providerId: string): Record<string, string> {
  return read()[providerId] ?? {};
}

export function setCredentialsFor(
  providerId: string,
  credentials: Record<string, string>,
): void {
  const store = read();
  store[providerId] = credentials;
  write(store);
}

export function clearCredentialsFor(providerId: string): void {
  const store = read();
  delete store[providerId];
  write(store);
}

/** True iff every required field for the provider has a non-empty value. */
export function hasAllCredentials(
  providerId: string,
  fields: CredentialField[],
): boolean {
  const creds = getCredentialsFor(providerId);
  return fields.every((f) => typeof creds[f.id] === "string" && creds[f.id].length > 0);
}
