import {
  editOriginalInteractionResponse,
  getOption,
  getUserId,
  InteractionResponseType,
  InteractionType,
  jsonResponse,
  verifyDiscordRequest,
} from "./discord";
import { createChatCompletion } from "./openai";
import { buildContext, buildSystemPrompt, buildUserPrompt, detectLanguage, fallbackAnswer, thinkingMessage } from "./prompts";
import { loadRecentHistory, retrieveChunks, saveConversationTurn } from "./rag";
import type { DiscordInteraction, Env, Language } from "./types";

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return handleHealth(env);
    }

    if (request.method === "GET") {
      return new Response("HolyBot Discord AI Worker is running.");
    }

    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const body = await request.text();
    const isValid = await verifyDiscordRequest(request, env, body);
    if (!isValid) {
      return new Response("Invalid request signature", { status: 401 });
    }

    const interaction = JSON.parse(body) as DiscordInteraction;

    if (interaction.type === InteractionType.Ping) {
      return jsonResponse({ type: InteractionResponseType.Pong });
    }

    if (interaction.type !== InteractionType.ApplicationCommand || interaction.data?.name !== "askholybot") {
      return jsonResponse({
        type: InteractionResponseType.ChannelMessageWithSource,
        data: { content: "Unsupported command.", flags: 64 },
      });
    }

    const question = getOption(interaction, "question")?.trim() ?? "";
    const requestedLanguage = getOption(interaction, "language") as Language | "auto" | undefined;
    const language = requestedLanguage && requestedLanguage !== "auto" ? requestedLanguage : detectLanguage(question);

    ctx.waitUntil(answerInteraction(env, interaction, question, language));

    return jsonResponse({
      type: InteractionResponseType.ChannelMessageWithSource,
      data: { content: thinkingMessage(language), flags: 64 },
    });
  },
};

async function handleHealth(env: Env): Promise<Response> {
  try {
    await env.DB.prepare("SELECT 1").first();

    return jsonResponse({
      name: "discord-ai-worker",
      status: "ok",
      dependencies: {
        d1: "ok",
        vectorize: "configured",
        openai: "configured",
        discord: "configured",
      },
    });
  } catch (error) {
    return jsonResponse(
      {
        name: "discord-ai-worker",
        status: "degraded",
        error: error instanceof Error ? error.message : String(error),
      },
      503,
    );
  }
}

async function answerInteraction(env: Env, interaction: DiscordInteraction, question: string, language: Language): Promise<void> {
  const userId = getUserId(interaction);
  const conversationId = `${interaction.guild_id ?? "dm"}:${userId}`;

  if (!question) {
    await editOriginalInteractionResponse(env, interaction, "Question is required.");
    return;
  }

  try {
    const chunks = await retrieveChunks(env, question, language);
    const context = buildContext(chunks);
    const history = await loadRecentHistory(env, conversationId);
    const answer = await createChatCompletion(env, [
      { role: "system", content: buildSystemPrompt(language, context) },
      ...history,
      { role: "user", content: buildUserPrompt(language, question) },
    ]);
    const finalAnswer = answer || fallbackAnswer(language);

    await saveConversationTurn(env, conversationId, userId, interaction.guild_id, language, question, finalAnswer);
    await editOriginalInteractionResponse(env, interaction, finalAnswer);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    await editOriginalInteractionResponse(env, interaction, `Error generating HolyBot answer: ${message}`);
  }
}
