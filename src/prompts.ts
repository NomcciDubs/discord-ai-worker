import type { Language, RetrievedChunk } from "./types";

export function detectLanguage(text: string): Language {
  const spanishHints = /\b(como|cómo|que|qué|para|puedo|servidor|instalar|ayuda|panel|mundo|archivo|contraseña|puerto|error|hacer|tengo|quiero|necesito)\b/i;
  return spanishHints.test(text) ? "es" : "en";
}

export function buildContext(chunks: RetrievedChunk[]): string {
  if (chunks.length === 0) {
    return "No relevant HolyHosting guide chunks were found.";
  }

  return chunks
    .map((chunk, index) => {
      return [
        `Guide #${index + 1}`,
        `Title: ${chunk.title}`,
        `Language: ${chunk.language}`,
        `Link: ${chunk.link}`,
        chunk.summary ? `Summary: ${chunk.summary}` : "",
        chunk.steps ? `Steps: ${chunk.steps}` : "",
        chunk.common_errors ? `Common errors: ${chunk.common_errors}` : "",
        `Content: ${chunk.content}`,
      ].filter(Boolean).join("\n");
    })
    .join("\n\n---\n\n");
}

export function buildSystemPrompt(language: Language, context: string): string {
  const languageRule = buildLanguageRule(language);

  return `You are HolyBot, the official support assistant for HolyHosting.

Critical rules:
1. Answer only about HolyHosting, the HolyHosting control panel, game hosting, Minecraft servers, mods, plugins, server files, configuration, and topics explicitly present in the provided guide context.
2. Use only the guide context below. Do not invent technical details, commands, policies, URLs, plans, prices, or panel features.
3. Do not invent URLs. Only include links that appear in the context.
4. If the context is not enough to answer accurately, say that there is not enough information in the HolyHosting guides and recommend contacting human support through the panel or Discord.
5. ${languageRule}
6. Be direct, practical, and use steps when useful.

HolyHosting guide context:
${context}`;
}

function buildLanguageRule(language: Language): string {
  if (language === "es") {
    return "Responde exclusivamente en español. Si el contexto está en inglés, traduce la información al español. No mezcles frases en inglés como 'Yes', 'Here is', 'Steps', or 'Common errors'.";
  }

  return "Answer exclusively in English. If the context is in Spanish, translate the information into English. Do not mix Spanish phrases such as 'Sí', 'Aquí tienes', 'Pasos', or 'Errores comunes'.";
}

export function fallbackAnswer(language: Language): string {
  if (language === "es") {
    return "No tengo información suficiente en las guías de HolyHosting para responder con exactitud. Por favor, contacta con nuestro equipo de soporte humano a través del panel o Discord.";
  }

  return "I do not have enough information in the HolyHosting guides to answer accurately. Please contact our human support team through the panel or Discord.";
}
