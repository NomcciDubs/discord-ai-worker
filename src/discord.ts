import * as ed from "@noble/ed25519";
import type { DiscordInteraction, Env } from "./types";

export const InteractionType = {
  Ping: 1,
  ApplicationCommand: 2,
} as const;

export const InteractionResponseType = {
  Pong: 1,
  ChannelMessageWithSource: 4,
  DeferredChannelMessageWithSource: 5,
} as const;

export async function verifyDiscordRequest(request: Request, env: Env, body: string): Promise<boolean> {
  const signature = request.headers.get("x-signature-ed25519");
  const timestamp = request.headers.get("x-signature-timestamp");

  if (!signature || !timestamp) return false;

  const message = new TextEncoder().encode(timestamp + body);
  return ed.verify(signature, message, env.DISCORD_PUBLIC_KEY);
}

export function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export function getOption(interaction: DiscordInteraction, name: string): string | undefined {
  return interaction.data?.options?.find((option) => option.name === name)?.value;
}

export function getUserId(interaction: DiscordInteraction): string {
  return interaction.member?.user?.id ?? interaction.user?.id ?? "unknown-user";
}

export async function editOriginalInteractionResponse(env: Env, interaction: DiscordInteraction, content: string): Promise<void> {
  const url = `https://discord.com/api/v10/webhooks/${env.DISCORD_APPLICATION_ID}/${interaction.token}/messages/@original`;
  const response = await fetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content: trimDiscordMessage(content) }),
  });

  if (!response.ok) {
    throw new Error(`Discord followup error ${response.status}: ${await response.text()}`);
  }
}

export function trimDiscordMessage(content: string): string {
  if (content.length <= 1900) return content;
  return `${content.slice(0, 1897)}...`;
}
