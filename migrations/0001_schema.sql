CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  language TEXT NOT NULL CHECK (language IN ('es', 'en')),
  title TEXT NOT NULL,
  link TEXT NOT NULL,
  content TEXT NOT NULL,
  summary TEXT,
  steps TEXT,
  keywords TEXT,
  common_errors TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_language_link
ON documents(language, link);

CREATE TABLE IF NOT EXISTS document_chunks (
  id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL,
  language TEXT NOT NULL CHECK (language IN ('es', 'en')),
  chunk_index INTEGER NOT NULL,
  title TEXT NOT NULL,
  link TEXT NOT NULL,
  content TEXT NOT NULL,
  summary TEXT,
  steps TEXT,
  keywords TEXT,
  common_errors TEXT,
  search_text TEXT NOT NULL,
  FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
ON document_chunks(document_id);

CREATE INDEX IF NOT EXISTS idx_document_chunks_language
ON document_chunks(language);

CREATE TABLE IF NOT EXISTS conversations (
  id TEXT PRIMARY KEY,
  discord_user_id TEXT NOT NULL,
  discord_guild_id TEXT,
  language TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation
ON conversation_messages(conversation_id, id);
