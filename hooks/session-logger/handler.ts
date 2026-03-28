import { writeFileSync, mkdirSync, existsSync } from "fs";
import { join } from "path";

const LOG_DIR = join(process.env.HOME || "/root", ".openclaw/workspace/logs");
const LOG_FILE = join(LOG_DIR, "session-events.log");

function timestamp() {
  return new Date().toISOString().replace("T", " ").slice(0, 19);
}

function appendLog(line: string) {
  try {
    if (!existsSync(LOG_DIR)) mkdirSync(LOG_DIR, { recursive: true });
    writeFileSync(LOG_FILE, line + "\n", { flag: "a" });
  } catch (e) {
    // silently fail
  }
}

export default async function handler(event: any) {
  const ts = timestamp();
  const sessionId = event.sessionId || event.session?.id || "unknown";
  const agentId = event.agentId || event.agent?.id || "unknown";
  const type = event.type || "unknown";
  const action = event.action || "";

  const line = `[${ts}] ${type}:${action} | session:${sessionId} | agent:${agentId}`;
  appendLog(line);
}
