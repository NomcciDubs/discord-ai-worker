import { execSync } from "node:child_process";
import process from "node:process";

const token = process.env.STATUS_INGEST_TOKEN;

if (!token) {
  console.log("Skipping status deploy report: STATUS_INGEST_TOKEN is not set.");
  process.exit(0);
}

const apiUrl = process.env.STATUS_API_URL ?? "https://status-api.nomcci.top/api/deploys";

const payload = {
  service: "discord-ai-worker",
  target: "worker",
  status: "success",
  commitSha: readGit("git rev-parse HEAD"),
  commitMessage: readGit("git log -1 --pretty=%s"),
  branch: process.env.CF_BRANCH ?? readGit("git branch --show-current"),
  environment: "production",
  ciProvider: "cloudflare",
  deployedAt: new Date().toISOString(),
};

const response = await fetch(apiUrl, {
  method: "POST",
  headers: {
    authorization: `Bearer ${token}`,
    "content-type": "application/json",
  },
  body: JSON.stringify(payload),
});

if (!response.ok) {
  throw new Error(`Status deploy report failed with ${response.status}: ${await response.text()}`);
}

console.log("Status deploy report sent.");

function readGit(command: string): string | undefined {
  try {
    return execSync(command, { encoding: "utf8" }).trim() || undefined;
  } catch {
    return undefined;
  }
}
