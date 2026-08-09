import "dotenv/config";

const applicationId = process.env.DISCORD_APPLICATION_ID;
const botToken = process.env.DISCORD_BOT_TOKEN;
const guildId = process.env.DISCORD_GUILD_ID;

if (!applicationId || !botToken) {
  throw new Error("Missing DISCORD_APPLICATION_ID or DISCORD_BOT_TOKEN in .env");
}

const command = {
  name: "askholybot",
  description: "Ask HolyBot a HolyHosting support question",
  type: 1,
  options: [
    {
      name: "question",
      description: "Your question in Spanish or English",
      type: 3,
      required: true,
    },
    {
      name: "language",
      description: "Answer language",
      type: 3,
      required: false,
      choices: [
        { name: "Auto", value: "auto" },
        { name: "Español", value: "es" },
        { name: "English", value: "en" },
      ],
    },
  ],
};

const scope = guildId ? `applications/${applicationId}/guilds/${guildId}` : `applications/${applicationId}`;
const url = `https://discord.com/api/v10/${scope}/commands`;

const response = await fetch(url, {
  method: "POST",
  headers: {
    Authorization: `Bot ${botToken}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify(command),
});

if (!response.ok) {
  throw new Error(`Discord command registration failed ${response.status}: ${await response.text()}`);
}

console.log(await response.json());
