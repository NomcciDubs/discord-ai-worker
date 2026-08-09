import type { Language, RetrievedChunk } from "./types";

export function detectLanguage(text: string): Language {
  const normalized = text.toLowerCase();
  const hasSpanishChars = /[áéíóúñ¿¡]/i.test(normalized);
  const spanishWords = normalized.match(/\b(hola|existe|alguna|manera|mejorar|paquete|como|cómo|que|qué|para|puedo|puedes|servidor|instalar|ayuda|panel|mundo|archivo|contraseña|puerto|error|hacer|tengo|quiero|necesito|mi|mis|el|la|los|las|un|una|de|del|en|con|por|servicio|cuenta|factura|soporte)\b/g) ?? [];
  const englishWords = normalized.match(/\b(hello|hi|how|what|can|could|server|install|help|world|file|password|port|error|do|have|want|need|my|the|a|an|of|in|with|for|service|account|invoice|support|upgrade|package)\b/g) ?? [];

  if (hasSpanishChars || spanishWords.length > englishWords.length) {
    return "es";
  }

  return "en";
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

export function buildUserPrompt(language: Language, question: string): string {
  if (language === "es") {
    return `Idioma obligatorio de la respuesta: español.
No respondas en inglés aunque el contexto o mensajes anteriores estén en inglés.

Pregunta del usuario:
${question}`;
  }

  return `Required answer language: English.
Do not answer in Spanish even if the context or previous messages are in Spanish.

User question:
${question}`;
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

export function thinkingMessage(language: Language): string {
  return language === "es" ? "HolyBot está pensando..." : "HolyBot is thinking...";
}
