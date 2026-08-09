# Discord AI Worker

Cloudflare Worker for a bilingual Discord support bot using OpenAI, D1, and Vectorize.

The default prompt is written for a HolyHosting-style support bot. Before reusing this project, update `src/prompts.ts` and `scripts/register-command.ts` so the bot identity, command name, and support rules match your own project.

## Architecture

```txt
Discord slash command
→ Cloudflare Worker verifies the request
→ OpenAI creates an embedding for the question
→ Vectorize finds relevant guide chunks
→ D1 loads readable content, summaries, links, and steps
→ OpenAI answers using that context
→ D1 stores the conversation turn
```

D1 is Cloudflare's serverless SQL database based on SQLite. This project uses it for guides, chunks, and conversation history.

Vectorize is Cloudflare's vector database. This project uses it for semantic search, so questions can match guides even when the wording is different.

## Setup

Install dependencies:

```bash
npm install
```

Create `.env`:

```bash
copy .env.example .env
```

Required values:

```env
DISCORD_PUBLIC_KEY=
DISCORD_APPLICATION_ID=
DISCORD_BOT_TOKEN=
DISCORD_GUILD_ID=
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

`DISCORD_GUILD_ID` is optional. Use it only if you want to register the slash command in one server for faster testing.

## Cloudflare

Wrangler is Cloudflare's CLI for Workers, D1, Vectorize, secrets, and deploys.

Create resources:

```bash
npx wrangler login
npx wrangler d1 create holybot-db
npx wrangler vectorize create holybot-index --dimensions=1536 --metric=cosine
npx wrangler vectorize create-metadata-index holybot-index --propertyName language --type string
```

Update `wrangler.toml` with the D1 `database_id` returned by Cloudflare.

Set secrets:

```bash
npx wrangler secret put DISCORD_PUBLIC_KEY
npx wrangler secret put DISCORD_APPLICATION_ID
npx wrangler secret put DISCORD_BOT_TOKEN
npx wrangler secret put OPENAI_API_KEY
```

Apply the schema and import generated data:

```bash
npm run db:migrate:remote
npx wrangler d1 execute holybot-db --remote --file data/generated/d1_import.sql
npx wrangler vectorize upsert holybot-index --file data/generated/vectorize_vectors.ndjson --batch-size 500
```

## Knowledge Pipeline

The Python tools read scraped Spanish and English guide JSON files. By default, `prepare_knowledge.py` reads from `../../Scriptsholy`.

```bash
npm run prepare-knowledge
npm run validate-knowledge
npm run summarize-knowledge
npm run build-d1-import
npm run embed-knowledge
```

Generated files go to `data/generated/`:

- `knowledge_chunks.jsonl`
- `knowledge_chunks_summarized.jsonl`
- `d1_import.sql`
- `vectorize_vectors.ndjson`

## Discord And Deploy

Register the slash command:

```bash
npm run register-command
```

Deploy:

```bash
npm run deploy
```

Then set the Discord Interactions Endpoint URL to the deployed Worker URL:

```txt
https://discord-ai-worker.<your-subdomain>.workers.dev
```

## CI/CD

You can connect this repository from the Cloudflare dashboard and deploy from GitHub.

Recommended settings if this folder is the repository root:

```txt
Build command: npm install && npm run typecheck
Deploy command: npm run deploy
```

If this project is inside a larger repository, set the Cloudflare project root to `discord-ai-worker`.

## Scripts

- `npm run dev`: run locally with Wrangler.
- `npm run deploy`: deploy to Cloudflare.
- `npm run typecheck`: validate TypeScript.
- `npm run register-command`: register `/askholybot` with Discord.
- `npm run prepare-knowledge`: normalize scraped JSON guides.
- `npm run summarize-knowledge`: generate summaries, steps, keywords, and common errors.
- `npm run build-d1-import`: generate the D1 SQL import file.
- `npm run embed-knowledge`: generate Vectorize embeddings.
- `npm run db:migrate:remote`: apply D1 migrations remotely.
