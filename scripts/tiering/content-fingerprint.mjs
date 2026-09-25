// Content fingerprint of one question: everything that must never change during tiering / referencing.
import crypto from "node:crypto";

export const IMMUTABLE_FIELDS = ["id", "text", "options", "correctOptionId", "image", "sources", "duplicateCount"];

export function contentHash(question) {
  const payload = Object.fromEntries(IMMUTABLE_FIELDS.map((field) => [field, question[field] ?? null]));
  return crypto.createHash("sha256").update(JSON.stringify(payload)).digest("hex");
}
