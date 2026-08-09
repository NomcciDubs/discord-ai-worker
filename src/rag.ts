import { createEmbedding } from "./openai";
import type { Env, Language, RetrievedChunk } from "./types";

export async function retrieveChunks(env: Env, question: string, language: Language): Promise<RetrievedChunk[]> {
  const vector = await createEmbedding(env, question);
  if (vector.length === 0) return [];

  const matches = await env.VECTORIZE.query(vector, {
    topK: 6,
    filter: { language },
    returnMetadata: "all",
  });

  const ids = matches.matches.map((match) => match.id);
  if (ids.length === 0) return [];

  const placeholders = ids.map(() => "?").join(", ");
  const query = `SELECT id, title, link, content, language, summary, steps, keywords, common_errors FROM document_chunks WHERE id IN (${placeholders})`;
  const rows = await env.DB.prepare(query).bind(...ids).all<RetrievedChunk>();

  const byId = new Map((rows.results ?? []).map((row) => [row.id, row]));

  const chunks: RetrievedChunk[] = [];
  for (const match of matches.matches) {
    const chunk = byId.get(match.id);
    if (chunk) {
      chunks.push({ ...chunk, score: match.score });
    }
  }

  return chunks;
}

export async function saveConversationTurn(
  env: Env,
  conversationId: string,
  userId: string,
  guildId: string | undefined,
  language: Language,
  question: string,
  answer: string,
): Promise<void> {
  await env.DB.prepare(
    `INSERT OR IGNORE INTO conversations (id, discord_user_id, discord_guild_id, language) VALUES (?, ?, ?, ?)`,
  )
    .bind(conversationId, userId, guildId ?? null, language)
    .run();

  await env.DB.batch([
    env.DB.prepare(`INSERT INTO conversation_messages (conversation_id, role, content) VALUES (?, 'user', ?)`).bind(
      conversationId,
      question,
    ),
    env.DB.prepare(`INSERT INTO conversation_messages (conversation_id, role, content) VALUES (?, 'assistant', ?)`).bind(
      conversationId,
      answer,
    ),
  ]);
}

export async function loadRecentHistory(env: Env, conversationId: string): Promise<Array<{ role: "user" | "assistant"; content: string }>> {
  const rows = await env.DB.prepare(
    `SELECT role, content FROM conversation_messages WHERE conversation_id = ? ORDER BY id DESC LIMIT 8`,
  )
    .bind(conversationId)
    .all<{ role: "user" | "assistant"; content: string }>();

  return (rows.results ?? []).reverse();
}
