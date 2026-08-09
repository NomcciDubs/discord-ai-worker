export interface Env {
  DB: D1Database;
  VECTORIZE: VectorizeIndex;
  DISCORD_PUBLIC_KEY: string;
  DISCORD_APPLICATION_ID: string;
  DISCORD_BOT_TOKEN: string;
  OPENAI_API_KEY: string;
  OPENAI_MODEL: string;
  OPENAI_EMBEDDING_MODEL: string;
}

export type Language = "es" | "en";

export interface DiscordInteraction {
  id: string;
  application_id: string;
  type: number;
  token: string;
  guild_id?: string;
  member?: { user?: { id: string } };
  user?: { id: string };
  data?: {
    name?: string;
    options?: Array<{ name: string; value: string }>;
  };
}

export interface RetrievedChunk {
  id: string;
  title: string;
  link: string;
  content: string;
  language: Language;
  summary?: string;
  steps?: string;
  keywords?: string;
  common_errors?: string;
  score?: number;
}
