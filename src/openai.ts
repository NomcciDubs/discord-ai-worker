import type { Env } from "./types";

interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export async function createEmbedding(env: Env, input: string): Promise<number[]> {
  const response = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: env.OPENAI_EMBEDDING_MODEL,
      input,
    }),
  });

  if (!response.ok) {
    throw new Error(`OpenAI embeddings error ${response.status}: ${await response.text()}`);
  }

  const data = (await response.json()) as { data: Array<{ embedding: number[] }> };
  return data.data[0]?.embedding ?? [];
}

export async function createChatCompletion(env: Env, messages: ChatMessage[]): Promise<string> {
  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: env.OPENAI_MODEL,
      messages,
      temperature: 0.2,
    }),
  });

  if (!response.ok) {
    throw new Error(`OpenAI chat error ${response.status}: ${await response.text()}`);
  }

  const data = (await response.json()) as { choices: Array<{ message: { content: string } }> };
  return data.choices[0]?.message.content?.trim() || "";
}
